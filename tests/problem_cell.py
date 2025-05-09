import cv2
import os

PNG_DIR = 'tests/png'
OUT_PATH = 'tests/cell_1.png'
OUT_PATH_SOLVED = 'tests/cell_4.png'
GRID_SIZE = 9
PADDING_FRAC = 0.2

# Get the second PNG file (grid2.png)
png_files = sorted([f for f in os.listdir(PNG_DIR) if f.endswith('.png')])
if len(png_files) < 2:
    raise RuntimeError('Not enough PNG files in tests/png/')
img_path = os.path.join(PNG_DIR, png_files[1])
img = cv2.imread(img_path)
if img is None:
    raise RuntimeError(f'Could not read {img_path}')

h, w = img.shape[:2]
cell_h = h // GRID_SIZE
cell_w = w // GRID_SIZE

# First problematic cell (row 3, col 2)
row, col = 3, 2  # 0-based
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
cv2.imwrite(OUT_PATH, cell_img)
print(f'Saved cell ({row},{col}) from {img_path} to {OUT_PATH}')

# Second cell two rows below (row 5, col 2)
row2 = row + 2
x1_2 = col * cell_w
y1_2 = row2 * cell_h
x2_2 = (col + 1) * cell_w
y2_2 = (row2 + 1) * cell_h
px1_2 = min(max(x1_2 + pad_x, 0), w)
py1_2 = min(max(y1_2 + pad_y, 0), h)
px2_2 = min(max(x2_2 - pad_x, 0), w)
py2_2 = min(max(y2_2 - pad_y, 0), h)
cell_img2 = img[py1_2:py2_2, px1_2:px2_2]
cv2.imwrite(OUT_PATH_SOLVED, cell_img2)
print(f'Saved cell ({row2},{col}) from {img_path} to {OUT_PATH_SOLVED}') 