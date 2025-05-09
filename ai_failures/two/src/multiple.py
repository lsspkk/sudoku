import cv2
import numpy as np
import pytesseract
import os
import sys
import traceback
import argparse
import re
from glob import glob

# BEST_OCR_SETTINGS holds the best OCR settings found by --teach mode in simple.py.
# These settings are used for all OCR operations in this script.
BEST_OCR_SETTINGS = {
    'psm': 6,
    'blur': None,
    'thresh': None,
    'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'
}

# Paths
IMG_PATH = 'logs/png/easy_sudoku_booklet_1_fi_4_p1_g1.png'
OUTPUT_TXT = 'logs/output.txt'
ANALYSIS_IMG = 'logs/analysis.png'
GRIDS_TXT = 'logs/grids.txt'
LOG_FILE = 'logs/multiple_error.log'
TEACH_FILE = 'pdf/easy_sudoku_booklet_1_fi_4.txt'

# Grid size
GRID_SIZE = 9
# Padding as a fraction of cell size (20%)
PADDING_FRAC = 0.2

def parse_teach_grid(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    in_grid = False
    grid = []
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('Grid 1:'):
            in_grid = True
            continue
        if in_grid:
            if line_stripped == '' or line_stripped.startswith('Grid 2:'):
                break
            if line_stripped.startswith('|'):
                blocks = [x.strip() for x in line_stripped[1:-1].split('|')]
                row = []
                for block in blocks:
                    row += [c for c in block.split(' ') if c]
                if len(row) == 9:
                    grid.append(row)
    if len(grid) != 9:
        raise ValueError(f'Parsed teach grid does not have 9 rows, got {len(grid)}')
    return grid

def process_image(img_path, grid_idx=None):
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f'Image not found: {img_path}')
    h, w = img.shape[:2]
    cell_h = h // GRID_SIZE
    cell_w = w // GRID_SIZE
    grid = [['-' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    output_lines = []
    recognized = []
    draw_img = img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
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
            cell_img = img[py1:py2, px1:px2]
            gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
            # Use best OCR settings
            img_proc = gray.copy()
            if BEST_OCR_SETTINGS['blur']:
                img_proc = cv2.GaussianBlur(img_proc, (BEST_OCR_SETTINGS['blur'], BEST_OCR_SETTINGS['blur']), 0)
            if BEST_OCR_SETTINGS['thresh']:
                _, img_proc = cv2.threshold(img_proc, BEST_OCR_SETTINGS['thresh'], 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            config = BEST_OCR_SETTINGS['config']
            text = pytesseract.image_to_string(img_proc, config=config).strip()
            if text.isdigit() and len(text) == 1:
                grid[row][col] = text
                cell_value = text
                recognized.append((row+1, col+1, text))
            else:
                cell_value = '-'
            output_lines.append(f'Cell ({row+1},{col+1}): {cell_value}')
            cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f'{row+1},{col+1}:{cell_value}'
            cv2.putText(draw_img, label, (x1+5, y1+cell_h//2), font, 0.5, (0,0,255), 1, cv2.LINE_AA)
    # Save analysis image if grid_idx is given
    if grid_idx is not None:
        analysis_img_path = f'logs/analysis_grid{grid_idx+1}.png'
        os.makedirs(os.path.dirname(analysis_img_path), exist_ok=True)
        cv2.imwrite(analysis_img_path, draw_img)
    return grid, output_lines

def write_single_grid_txt(grid, idx, mode='a'):
    lines = []
    lines.append(f'Grid {idx+1}:')
    lines.append('=========================')
    lines.append('+-------+-------+-------+')
    for i in range(GRID_SIZE):
        row_cells = [(grid[i][j] if grid[i][j] != '-' else '-') for j in range(GRID_SIZE)]
        row_str = '| ' + ' '.join(row_cells[0:3]) + ' | ' + ' '.join(row_cells[3:6]) + ' | ' + ' '.join(row_cells[6:9]) + ' |'
        lines.append(row_str)
        if i % 3 == 2:
            lines.append('+-------+-------+-------+')
    lines.append('')
    with open(GRIDS_TXT, mode) as f:
        f.write('\n'.join(lines))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--multiple', action='store_true', help='Process all PNG files in logs/png')
    parser.add_argument('--grids', type=int, default=None, help='Process only the first N PNG files')
    args = parser.parse_args()
    try:
        if args.multiple:
            png_files = sorted(glob('logs/png/*.png'))
            if args.grids is not None:
                png_files = png_files[:args.grids]
            # Clear grids.txt at the start
            open(GRIDS_TXT, 'w').close()
            for idx, png_file in enumerate(png_files):
                print(f'Processing {png_file}...')
                grid, _ = process_image(png_file, grid_idx=idx)
                write_single_grid_txt(grid, idx, mode='a')
            print(f'Processed {len(png_files)} grids. Output written to {GRIDS_TXT}')
        else:
            grid, output_lines = process_image(IMG_PATH)
            os.makedirs(os.path.dirname(OUTPUT_TXT), exist_ok=True)
            with open(OUTPUT_TXT, 'w') as f:
                f.write('\n'.join(output_lines))
            os.makedirs(os.path.dirname(ANALYSIS_IMG), exist_ok=True)
            cv2.imwrite(ANALYSIS_IMG, cv2.imread(IMG_PATH))
            # Clear and write single grid
            open(GRIDS_TXT, 'w').close()
            write_single_grid_txt(grid, 0, mode='a')
            print(f'Processed 1 grid. Output written to {GRIDS_TXT}')
    except Exception as e:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            f.write(traceback.format_exc())
        print(f"Error occurred. See {LOG_FILE} for details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 