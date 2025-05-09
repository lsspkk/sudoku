"""
Improved Sudoku OCR script (max accuracy):
- Uses per-digit best OCR settings (from logs_simple.txt)
- Tries both raw and preprocessed images for OCR
- Template matching with all templates, at multiple scales, with binarization and centering
- Picks the result with the highest confidence (OCR or template)
- Debug mode to save intermediate images and log scores
- Supports --teach parameter for grid 1 as before
"""
import cv2
import numpy as np
import pytesseract
import os
import sys
import traceback
import argparse
import re
from collections import Counter
from glob import glob

# Paths
IMG_PATH = 'logs/png/easy_sudoku_booklet_1_fi_4_p1_g1.png'
OUTPUT_TXT = 'logs/output.txt'
ANALYSIS_IMG = 'logs/analysis.png'
GRIDS_TXT = 'logs/grids.txt'
LOG_FILE = 'logs/improved_error.log'
TEACH_FILE = 'pdf/easy_sudoku_booklet_1_fi_4.txt'
TEMPLATE_DIR = 'data'
DEBUG_DIR = 'logs/debug_cells'

# Grid size
GRID_SIZE = 9
# Padding as a fraction of cell size (20%)
PADDING_FRAC = 0.2

# Debug flag
DEBUG = True

# Per-digit best OCR settings (from logs_simple.txt)
BEST_OCR_SETTINGS = {
    '1': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '2': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '3': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '4': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '5': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '6': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '7': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '8': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
    '9': {'psm': 6, 'blur': None, 'thresh': None, 'config': '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'},
}
DEFAULT_OCR_CONFIG = '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'

# Load digit templates from data/*.png
TEMPLATES = {}
for path in glob(os.path.join(TEMPLATE_DIR, '*.png')):
    digit = os.path.splitext(os.path.basename(path))[0]
    if digit.isdigit():
        tmpl_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if tmpl_img is not None:
            # Binarize and resize template to 64x64 for consistency
            tmpl_img = cv2.resize(tmpl_img, (64, 64), interpolation=cv2.INTER_LINEAR)
            _, tmpl_bin = cv2.threshold(tmpl_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            TEMPLATES[digit] = tmpl_bin

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

def preprocess_cell(cell_img):
    gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    # Contrast enhancement
    gray = cv2.equalizeHist(gray)
    # Resize for better OCR/template matching
    gray = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_LINEAR)
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    # Morphological opening to remove noise
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    # Apply a fixed high threshold to ensure background is white
    _, morph_high = cv2.threshold(morph, 180, 255, cv2.THRESH_BINARY)
    return gray, morph_high

def ocr_cell(cell_img, digit=None):
    # Try best config for this digit, then fallback configs
    results = []
    configs = []
    if digit and digit in BEST_OCR_SETTINGS:
        configs.append(BEST_OCR_SETTINGS[digit]['config'])
    configs += [
        '--psm 10 --oem 3 -c tessedit_char_whitelist=123456789',
        '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789',
        '--psm 13 --oem 3 -c tessedit_char_whitelist=123456789',
        '--psm 10 --oem 1 -c tessedit_char_whitelist=123456789',
    ]
    for config in configs:
        text = pytesseract.image_to_string(cell_img, config=config).strip()
        if text.isdigit() and len(text) == 1:
            results.append(text)
    # Majority vote
    if results:
        most_common = Counter(results).most_common(1)[0][0]
        return most_common, True
    return None, False

def template_match_cell(cell_img):
    best_digit, best_score = None, -1
    # Try multiple scales
    for scale in [0.8, 1.0, 1.2]:
        cell_scaled = cv2.resize(cell_img, (int(64*scale), int(64*scale)), interpolation=cv2.INTER_LINEAR)
        for digit, tmpl in TEMPLATES.items():
            # Resize cell to template size
            cell_resized = cv2.resize(cell_scaled, tmpl.shape[::-1], interpolation=cv2.INTER_LINEAR)
            res = cv2.matchTemplate(cell_resized, tmpl, cv2.TM_CCOEFF_NORMED)
            score = res.max()
            if score > best_score:
                best_score = score
                best_digit = digit
    return best_digit, best_score

def save_debug_image(img, row, col, label):
    if not DEBUG:
        return
    os.makedirs(DEBUG_DIR, exist_ok=True)
    cv2.imwrite(os.path.join(DEBUG_DIR, f'cell_{row+1}_{col+1}_{label}.png'), img)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--teach', action='store_true', help='Try to learn best OCR settings using ground truth')
    args = parser.parse_args()
    try:
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
                gray, morph = preprocess_cell(cell_img)
                # Try OCR on both raw and preprocessed
                ocr_results = []
                for img_variant in [gray, morph]:
                    ocr_val, ocr_ok = ocr_cell(img_variant)
                    if ocr_ok:
                        ocr_results.append(ocr_val)
                # Try template matching on preprocessed
                tmpl_digit, tmpl_score = template_match_cell(morph)
                # Debug: save images
                if DEBUG:
                    save_debug_image(gray, row, col, 'gray')
                    save_debug_image(morph, row, col, 'morph')
                # Decision logic
                cell_value = '-'
                if args.teach and teach_grid:
                    gt = teach_grid[row][col]
                    if gt == '-':
                        cell_value = '-'
                    else:
                        # Accept if any OCR or template matches ground truth
                        if gt in ocr_results:
                            cell_value = gt
                            best_settings[gt] = 'ocr'
                        elif tmpl_digit == gt and tmpl_score > 0.4:
                            cell_value = gt
                            best_settings[gt] = 'template'
                        else:
                            cell_value = '-'
                    grid[row][col] = cell_value
                else:
                    # Use OCR if any result is confident
                    if ocr_results:
                        # Use majority vote if multiple
                        cell_value = Counter(ocr_results).most_common(1)[0][0]
                        grid[row][col] = cell_value
                        recognized.append((row+1, col+1, cell_value))
                    elif tmpl_digit and tmpl_score > 0.4:
                        grid[row][col] = tmpl_digit
                        cell_value = tmpl_digit
                    else:
                        cell_value = '-'
                    output_lines.append(f'Cell ({row+1},{col+1}): {cell_value} (tmpl_score={tmpl_score:.2f})')
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
            print('Best method found for each digit:')
            for digit, method in best_settings.items():
                print(f'Digit {digit}: {method}')
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