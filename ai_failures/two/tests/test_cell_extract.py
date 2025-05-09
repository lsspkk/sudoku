#!/usr/bin/env python
import os
import sys
import unittest
import cv2

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cell_extract import CellExtractor
from src.png_grid_extractor import PNGGridExtractor

class TestCellExtractorGrid1(unittest.TestCase):
    def test_extract_grid1_against_reference(self):
        """Test extraction of grid 1 and compare to reference solution."""
        # Path to the PNG and reference solution
        grid_png = os.path.join('logs', 'png', 'easy_sudoku_booklet_1_fi_4_p1_g1.png')
        reference_txt = os.path.join('pdf', 'easy_sudoku_booklet_1_fi_4.txt')
        self.assertTrue(os.path.exists(grid_png), f"Grid PNG not found: {grid_png}")
        self.assertTrue(os.path.exists(reference_txt), f"Reference TXT not found: {reference_txt}")

        # Load the reference grid (first grid only)
        reference_grid = []
        with open(reference_txt, 'r') as f:
            in_grid = False
            for line in f:
                if line.strip().startswith('Grid 1:'):
                    in_grid = True
                    continue
                if in_grid:
                    if line.strip().startswith('+'):
                        continue
                    if not line.strip() or line.strip().startswith('Grid'):
                        break
                    # Parse row: | - - - | 1 - - | - - - |
                    row = []
                    parts = line.strip().split('|')[1:-1]  # skip first and last |
                    for part in parts:
                        for cell in part.strip().split():
                            if cell == '-':
                                row.append(None)
                            else:
                                try:
                                    row.append(int(cell))
                                except Exception:
                                    row.append(None)
                    if row:
                        reference_grid.append(row)
        self.assertEqual(len(reference_grid), 9, "Reference grid should have 9 rows")
        for row in reference_grid:
            self.assertEqual(len(row), 9, "Each reference grid row should have 9 columns")

        # Load the grid image
        image = cv2.imread(grid_png)
        self.assertIsNotNone(image, f"Could not read image: {grid_png}")

        # Initialize CellExtractor
        extractor = CellExtractor(config_path='config/ocr_settings.yaml')
        # Use PNGGridExtractor's grid detection
        grid_cells = PNGGridExtractor().detect_grid(image)
        self.assertIsNotNone(grid_cells, "Failed to detect grid in image")
        # Extract numbers
        grid_numbers = []
        for row in range(9):
            number_row = []
            for col in range(9):
                x, y, w, h = grid_cells[row][col]
                # For cell (1,0), call analyze_cell first and print the best result
                if row == 1 and col == 0:
                    best_result = extractor.analyze_cell(image, x, y, w, h)
                    print(f"ANALYZE cell (1,0) best result: {best_result}")
                result = extractor.extract_cell(image, x, y, w, h)
                number_row.append(result['number'])
            grid_numbers.append(number_row)
        # Compare to reference
        for i in range(9):
            for j in range(9):
                self.assertEqual(
                    grid_numbers[i][j], reference_grid[i][j],
                    f"Mismatch at cell ({i},{j}): extracted={grid_numbers[i][j]}, expected={reference_grid[i][j]}"
                )

if __name__ == '__main__':
    unittest.main() 