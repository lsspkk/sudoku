import os
import re
import cv2
import numpy as np
from collections import defaultdict

LOG_PATH = 'logs/extract_cell.log'
PNG_DIR = 'logs/png'
OUTPUT_DIR = 'logs'
PNG_GRID_LOG = 'logs/png_grid_extractor.log'

# Regex to parse log lines for cell extraction
CELL_LOG_RE = re.compile(r"extract_cell.*grid_number=(\d+).*row=(\d+).*col=(\d+).*x=(\d+).*y=(\d+).*w=(\d+).*h=(\d+).*(number=([\d]+|None))?")
# Regex to map grid_number to PNG file from png_grid_extractor.log
GRID_PNG_RE = re.compile(r"Grid (\d+): (.+\.png), image shape:.*extract_cell calls: (\d+)")

# Map grid_number to list of cell info
grid_cells = defaultdict(list)
# Map grid_number to PNG file
grid_to_png = {}

# Parse the png_grid_extractor.log to map grid_number to PNG file
if os.path.exists(PNG_GRID_LOG):
    with open(PNG_GRID_LOG, 'r') as f:
        for line in f:
            m = GRID_PNG_RE.search(line)
            if m:
                grid_number = int(m.group(1))
                png_file = m.group(2).strip()
                grid_to_png[grid_number] = png_file
else:
    print(f"Warning: {PNG_GRID_LOG} not found. Will use fallback PNG search.")

# Parse the extract_cell.log file
with open(LOG_PATH, 'r') as f:
    for line in f:
        m = CELL_LOG_RE.search(line)
        if m:
            grid_number = int(m.group(1))
            row = int(m.group(2))
            col = int(m.group(3))
            x = int(m.group(4))
            y = int(m.group(5))
            w = int(m.group(6))
            h = int(m.group(7))
            number = m.group(9)
            grid_cells[grid_number].append({
                'row': row, 'col': col, 'x': x, 'y': y, 'w': w, 'h': h, 'number': number
            })

print(f"Parsed grids: {list(grid_cells.keys())}")
processed = 0
# For each grid, find the corresponding PNG file and draw boxes
for grid_number, cells in grid_cells.items():
    # Use mapping from png_grid_extractor.log if available
    png_file = None
    if grid_number in grid_to_png:
        png_file = grid_to_png[grid_number]
        if not os.path.isabs(png_file):
            png_file = os.path.join(PNG_DIR, os.path.basename(png_file))
        print(f"Grid {grid_number}: Using PNG from log: {png_file}")
    else:
        print(f"Looking for PNG for grid {grid_number} in {PNG_DIR}")
        png_candidates = [f for f in os.listdir(PNG_DIR) if f"grid{grid_number}" in f and f.endswith('.png')]
        print(f"  Candidates: {png_candidates}")
        if not png_candidates:
            print(f"No PNG file found for grid {grid_number}")
            continue
        png_file = os.path.join(PNG_DIR, png_candidates[0])
        print(f"  Using PNG file: {png_file}")
    image = cv2.imread(png_file)
    if image is None:
        print(f"Failed to load image: {png_file}")
        continue
    print(f"  Loaded image shape: {image.shape}")
    # Draw rectangles for each cell
    for cell in cells:
        x, y, w, h = cell['x'], cell['y'], cell['w'], cell['h']
        number = cell['number']
        color = (0, 255, 0) if number and number != 'None' else (0, 0, 255)
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        label = f"({cell['row']},{cell['col']})"
        if number and number != 'None':
            label += f":{number}"
        cv2.putText(image, label, (x + 2, y + h - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    # Save the annotated image
    out_path = os.path.join(OUTPUT_DIR, f"grid{grid_number}_analysis.png")
    cv2.imwrite(out_path, image)
    print(f"Saved {out_path}")
    processed += 1

if processed == 0:
    print("No images were processed. Check log parsing, PNG file presence, and image loading.")
else:
    print(f"Done. {processed} grid images processed and saved.") 