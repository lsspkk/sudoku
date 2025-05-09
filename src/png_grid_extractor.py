import os
print(f"[DEBUG] Running: {os.path.abspath(__file__)}")
import sys
import cv2
import logging
from glob import glob
from cell_extract import extract_and_recognize_cell
import time
import argparse
import re

TEMPLATE_DIR = 'data'
PNG_DIR = 'tests/png'
LOGS_DIR = 'logs'
GRIDS_TXT = os.path.join(LOGS_DIR, 'grids.txt')
LOG_FILE = os.path.join(LOGS_DIR, 'png_grid_extractor.log')
GRID_SIZE = 9
PADDING_FRAC = 0.2

# Setup logging
os.makedirs(LOGS_DIR, exist_ok=True)
# Empty the log file at start
with open(LOG_FILE, 'w') as f:
    pass
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(levelname)s %(message)s')

# Empty the grids.txt at start
with open(GRIDS_TXT, 'w') as f:
    pass

# Load templates
import numpy as np
TEMPLATES = {}
for path in glob(os.path.join(TEMPLATE_DIR, '*.png')):
    digit = os.path.splitext(os.path.basename(path))[0]
    if digit.isdigit():
        tmpl_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if tmpl_img is not None:
            tmpl_img = cv2.resize(tmpl_img, (64, 64), interpolation=cv2.INTER_LINEAR)
            _, tmpl_bin = cv2.threshold(tmpl_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            TEMPLATES[digit] = tmpl_bin

timing_info = {'start_time': None, 'file_times': [], 'total_files': 0}

def format_hms(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def calculate_timing(idx, total_files, file_time):
    global timing_info
    if timing_info['start_time'] is None:
        timing_info['start_time'] = time.time()
    timing_info['file_times'].append(file_time)
    timing_info['total_files'] = total_files
    elapsed = time.time() - timing_info['start_time']
    mean_time = sum(timing_info['file_times']) / len(timing_info['file_times']) if timing_info['file_times'] else 0
    files_left = total_files - (idx + 1)
    est_time_left = files_left * mean_time
    return {
        'current_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed': elapsed,
        'mean_time': mean_time,
        'files_left': files_left,
        'est_time_left': est_time_left,
        'current_idx': idx + 1,
        'total_files': total_files
    }

def log_timing(timing):
    log_line = (f"File {timing['current_idx']}/{timing['total_files']} | "
                f"Timing {timing['current_time']} | Elapsed: {format_hms(timing['elapsed'])} | "
                f"Mean/file: {timing['mean_time']:.1f}s | Files left: {timing['files_left']} | "
                f"Est. time left: {format_hms(timing['est_time_left'])}")
    logging.info(log_line)
    print(log_line)

def process_grid_image(img_path, templates):
    grid_start_time = time.time()
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f'Image not found: {img_path}')
    h, w = img.shape[:2]
    cell_h = h // GRID_SIZE
    cell_w = w // GRID_SIZE
    grid = [['-' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x1 = col * cell_w
            y1 = row * cell_h
            x2 = (col + 1) * cell_w
            y2 = (row + 1) * cell_h
            pad_x = int(cell_w * PADDING_FRAC)
            pad_y = int(cell_h * PADDING_FRAC)
            px1 = min(max(x1 + pad_x, 0), w)
            py1 = min(max(y1 + pad_y, 0), h)
            px2 = min(max(x2 - pad_x, 0), w)
            py2 = min(max(y2 - pad_y, 0), h)
            try:
                cell_start_time = time.time()
                val, reliability, ocr_count = extract_and_recognize_cell(
                    img, px1, py1, px2-px1, py2-py1, templates=templates)
                cell_time = time.time() - cell_start_time
                logging.info(f'Cell ({row},{col}) extraction time: {cell_time:.3f}s (time in seconds to extract and recognize this cell)')
                ocr_timing_str = f"ocr_timing={cell_time:.1f}s"
                if val == '-':
                    logging.info(f'Cell ({row},{col}) at (x={px1}, y={py1}, w={px2-px1}, h={py2-py1}): empty {ocr_timing_str}')
                else:
                    logging.info(f'Cell ({row},{col}) at (x={px1}, y={py1}, w={px2-px1}, h={py2-py1}): {val} (reliability={reliability}, ocr_count={ocr_count}) {ocr_timing_str}')
            except Exception as e:
                logging.error(f'Cell ({row},{col}) in {img_path} failed: {e}')
                val = '-'
            grid[row][col] = val
    grid_time = time.time() - grid_start_time
    logging.info(f'Grid extraction time for {img_path}: {grid_time:.3f}s (time in seconds to extract and recognize all cells in this grid)')
    return grid

# example png valuelogs/png/easy_sudoku_booklet_1_fi_4_p10_g4.png
# g4 is grid 4
# p10 is page 10
# source is easy_sudoku_booklet_1_fi_4
# path is logs/png
# 
# parses clean grid name that is <source>, sivu <page> - Ruudukko <grid>
def make_grid_name(idx, png_file):
    without_path = os.path.basename(png_file)
    without_ext = os.path.splitext(without_path)[0]
    parts = without_ext.split('_')
    page = ''
    grid = ''
    source = ''
    for part in parts:
        if part.startswith('g'):
            grid = part[1:]
        elif part.startswith('p'):
            page = part[1:]
        elif source == '':
            source = part
        else:
            source += f'_{part}'
    if source is '':
        source = 'Tuntematon'
    if page is not '':
        page = f', sivu {page}'
    if grid is not '':
        grid = f' - numero {grid}'
    return f'{source}{page}{grid}'


def write_grid_txt(grid, idx, png_file):
    lines = []
    grid_name = make_grid_name(idx, png_file)
    
    lines.append(f'Source file: {png_file}' )
    lines.append(f'Ruudukko: {grid_name}')
    lines.append('+-------+-------+-------+')
    for i in range(GRID_SIZE):
        row_cells = [(grid[i][j] if grid[i][j] != '-' else '-') for j in range(GRID_SIZE)]
        row_str = '| ' + ' '.join(row_cells[0:3]) + ' | ' + ' '.join(row_cells[3:6]) + ' | ' + ' '.join(row_cells[6:9]) + ' |'
        lines.append(row_str)
        if i % 3 == 2:
            lines.append('+-------+-------+-------+')
    lines.append('')
    with open(GRIDS_TXT, 'a') as f:
        f.write('\n'.join(lines) + '\n')

def pad_page_and_grid(filename):
    # Pad page and grid numbers with zeros for sorting and display
    def pad(match):
        return f"_{match.group(1)}{int(match.group(2)):02d}{match.group(3)}"
    # Pad _p<number>_
    filename = re.sub(r'(_p)(\d+)(_)', pad, filename)
    # Pad _g<number>.png
    filename = re.sub(r'(_g)(\d+)(\.png)', pad, filename)
    return filename

def extract_page_and_grid(filename):
    # Example: easy_sudoku_booklet_1_fi_4_p10_g4.png
    m = re.search(r'_p(\d+)_g(\d+)', filename)
    if m:
        return int(m.group(1)), int(m.group(2))
    return (float('inf'), float('inf'))

def main():
    parser = argparse.ArgumentParser(description='Extract Sudoku grids from PNG files or folders')
    parser.add_argument('input', help='PNG file or folder to process (required)')
    args = parser.parse_args()

    if os.path.isdir(args.input):
        png_files = glob(os.path.join(args.input, '*.png'))
        # Sort by padded filename for lexicographical order
        png_files.sort(key=lambda f: pad_page_and_grid(os.path.basename(f)))
        print(f"Found {len(png_files)} PNG files in {args.input}.")
    elif os.path.isfile(args.input) and args.input.lower().endswith('.png'):
        png_files = [args.input]
        print(f"Processing single PNG file: {args.input}")
    else:
        print(f"Input {args.input} is not a valid PNG file or directory.")
        return

    global timing_info
    timing_info['start_time'] = time.time()
    timing_info['file_times'] = []
    timing_info['total_files'] = len(png_files)

    total_start_time = time.time()
    all_grids = []
    for idx, png_file in enumerate(png_files):
        print(f"[{idx+1}/{len(png_files)}] Processing {png_file}...")
        logging.info(f'Processing {png_file}...')
        file_start = time.time()
        try:
            grid = process_grid_image(png_file, TEMPLATES)
            all_grids.append(grid)
            write_grid_txt(grid, idx, png_file)
        except Exception as e:
            logging.error(f'Failed to process {png_file}: {e}')
            print(f"Error processing {png_file}: {e}")
        file_time = time.time() - file_start
        timing = calculate_timing(idx, len(png_files), file_time)
        log_timing(timing)
    total_time = time.time() - total_start_time
    print(f"\nAll done! Total elapsed time: {format_hms(total_time)}")
    logging.info(f'Total script time: {total_time:.3f}s (time in seconds to process all grids in this run)')
    print(f'Processed {len(all_grids)} grids. Output written to {GRIDS_TXT}')

if __name__ == '__main__':
    main()
