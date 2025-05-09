import os
import cv2
import re

PNG_DIR = 'tests/png'
OUT_DIR = 'tests/cells'
LOG_DIFF = 'tests/log_diff_report.txt'
GRID_SIZE = 9
PADDING_FRAC = 0.2

os.makedirs(OUT_DIR, exist_ok=True)

with open(LOG_DIFF, 'r') as f:
    for line in f:
        m = re.match(r"Grid (\d+) Cell \((\d+),(\d+)\): expected '(.+?)', actual '(.+?)'", line)
        if not m:
            continue
        grid_n = int(m.group(1))
        x = int(m.group(3))
        y = int(m.group(2))
        expected = m.group(4)
        actual = m.group(5)
        png_path = os.path.join(PNG_DIR, f'grid{grid_n}.png')
        if not os.path.exists(png_path):
            print(f"PNG not found: {png_path}")
            continue
        img = cv2.imread(png_path)
        if img is None:
            print(f"Could not read {png_path}")
            continue
        h, w = img.shape[:2]
        cell_h = h // GRID_SIZE
        cell_w = w // GRID_SIZE
        x1 = x * cell_w
        y1 = y * cell_h
        x2 = (x + 1) * cell_w
        y2 = (y + 1) * cell_h
        pad_x = int(cell_w * PADDING_FRAC)
        pad_y = int(cell_h * PADDING_FRAC)
        px1 = min(max(x1 + pad_x, 0), w)
        py1 = min(max(y1 + pad_y, 0), h)
        px2 = min(max(x2 - pad_x, 0), w)
        py2 = min(max(y2 - pad_y, 0), h)
        cell_img = img[py1:py2, px1:px2]
        out_name = f'grid_{grid_n}_x_{x}_y_{y}_expected_a_{expected}_actual_b_{actual}.png'
        out_path = os.path.join(OUT_DIR, out_name)
        cv2.imwrite(out_path, cell_img)
        print(f'Saved {out_path}') 