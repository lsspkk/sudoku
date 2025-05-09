from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.insert(0, os.getenv('PYTHONPATH', 'src'))
import cv2
from glob import glob
from cell_extract import extract_and_recognize_cell
import pytest

TEMPLATE_DIR = 'data'
PNG_DIR = 'tests/png'
EXPECTED_GRIDS = 'tests/grids_expected.txt'
GRID_SIZE = 9
PADDING_FRAC = 0.2

# Load templates
TEMPLATES = {}
for path in glob(os.path.join(TEMPLATE_DIR, '*.png')):
    digit = os.path.splitext(os.path.basename(path))[0]
    if digit.isdigit():
        tmpl_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if tmpl_img is not None:
            tmpl_img = cv2.resize(tmpl_img, (64, 64), interpolation=cv2.INTER_LINEAR)
            _, tmpl_bin = cv2.threshold(tmpl_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            TEMPLATES[digit] = tmpl_bin

def parse_expected_grids(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    grids = []
    grid = []
    for line in lines:
        line = line.strip()
        if line.startswith('Grid'):
            if grid:
                grids.append(grid)
                grid = []
        elif line.startswith('|'):
            blocks = [x.strip() for x in line[1:-1].split('|')]
            row = []
            for block in blocks:
                row += [c for c in block.split(' ') if c]
            if len(row) == 9:
                grid.append(row)
    if grid:
        grids.append(grid)
    return grids

def test_cell_extract():
    expected_grids = parse_expected_grids(EXPECTED_GRIDS)
    png_files = sorted(glob(os.path.join(PNG_DIR, '*.png')))
    assert len(expected_grids) == len(png_files), "Number of expected grids and PNG files must match."
    for grid_idx, (png_file, expected_grid) in enumerate(zip(png_files, expected_grids)):
        img = cv2.imread(png_file)
        h, w = img.shape[:2]
        cell_h = h // GRID_SIZE
        cell_w = w // GRID_SIZE
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
                actual = extract_and_recognize_cell(img, px1, py1, px2-px1, py2-py1, templates=TEMPLATES)
                expected = expected_grid[row][col]
                assert actual == expected, f"Grid {grid_idx+1} Cell ({row+1},{col+1}): expected '{expected}', got '{actual}' in {png_file}" 