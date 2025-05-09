import cv2
import numpy as np
import pytesseract
import os
import sys
import traceback
import argparse
import re

# Paths
IMG_PATH = 'logs/png/easy_sudoku_booklet_1_fi_4_p1_g1.png'
OUTPUT_TXT = 'logs/output.txt'
ANALYSIS_IMG = 'logs/analysis.png'
GRIDS_TXT = 'logs/grids.txt'
LOG_FILE = 'logs/simple_error.log'
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

def try_ocr_settings(cell_img, settings_list):
    best = {'text': '', 'score': 0, 'settings': None}
    for settings in settings_list:
        img = cell_img.copy()
        # Preprocessing
        if settings.get('blur'):
            img = cv2.GaussianBlur(img, (settings['blur'], settings['blur']), 0)
        if settings.get('thresh'):
            _, img = cv2.threshold(img, settings['thresh'], 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        config = settings['config']
        text = pytesseract.image_to_string(img, config=config).strip()
        if text.isdigit() and len(text) == 1:
            return {'text': text, 'score': 1, 'settings': settings}
        # Optionally, could score partial matches
    return best

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--teach', action='store_true', help='Try to learn best OCR settings using ground truth')
    args = parser.parse_args()
    try:
        # Load image
        img = cv2.imread(IMG_PATH)
        if img is None:
            raise FileNotFoundError(f'Image not found: {IMG_PATH}')
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
        best_settings = {}
        teach_grid = None
        if args.teach:
            teach_grid = parse_teach_grid(TEACH_FILE)
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
                if args.teach and teach_grid:
                    gt = teach_grid[row][col]
                    if gt == '-':
                        cell_value = '-'
                    else:
                        # Try multiple settings
                        settings_list = []
                        for psm in [6, 10, 13]:
                            for blur in [0, 3, 5]:
                                for thresh in [0, 127, 180]:
                                    config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=123456789'
                                    settings = {'psm': psm, 'blur': blur if blur else None, 'thresh': thresh if thresh else None, 'config': config}
                                    settings_list.append(settings)
                        # Try at least 10 settings
                        settings_list = settings_list[:max(10, len(settings_list))]
                        best = None
                        for settings in settings_list:
                            img_proc = gray.copy()
                            if settings['blur']:
                                img_proc = cv2.GaussianBlur(img_proc, (settings['blur'], settings['blur']), 0)
                            if settings['thresh']:
                                _, img_proc = cv2.threshold(img_proc, settings['thresh'], 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                            config = settings['config']
                            text = pytesseract.image_to_string(img_proc, config=config).strip()
                            if text == gt:
                                best = settings
                                break
                        if best:
                            cell_value = gt
                            best_settings[gt] = best
                        else:
                            cell_value = '-'
                    grid[row][col] = cell_value
                else:
                    blur = cv2.GaussianBlur(gray, (3, 3), 0)
                    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    config = '--psm 10 --oem 3 -c tessedit_char_whitelist=123456789'
                    text = pytesseract.image_to_string(thresh, config=config)
                    text = text.strip()
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
        os.makedirs(os.path.dirname(OUTPUT_TXT), exist_ok=True)
        with open(OUTPUT_TXT, 'w') as f:
            f.write('\n'.join(output_lines))
        os.makedirs(os.path.dirname(ANALYSIS_IMG), exist_ok=True)
        cv2.imwrite(ANALYSIS_IMG, draw_img)
        lines = []
        lines.append('Grid 1:')
        lines.append('+-------+-------+-------+')
        for i in range(GRID_SIZE):
            row_cells = [(grid[i][j] if grid[i][j] != '-' else '-') for j in range(GRID_SIZE)]
            row_str = '| ' + ' '.join(row_cells[0:3]) + ' | ' + ' '.join(row_cells[3:6]) + ' | ' + ' '.join(row_cells[6:9]) + ' |'
            lines.append(row_str)
            if i % 3 == 2:
                lines.append('+-------+-------+-------+')
        with open(GRIDS_TXT, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        if args.teach:
            print('Best OCR settings found for each digit:')
            for digit, settings in best_settings.items():
                print(f'Digit {digit}: {settings}')
        else:
            print(f"Recognized {len(recognized)} numbers:")
            for r, c, v in recognized:
                print(f"  Cell ({r},{c}): {v}")
            print(f"Output written to {OUTPUT_TXT}, {ANALYSIS_IMG}, {GRIDS_TXT}")
    except Exception as e:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            f.write(traceback.format_exc())
        print(f"Error occurred. See {LOG_FILE} for details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 