import cv2
import numpy as np
from pathlib import Path
import logging
import json
import sys
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_number_reader_v1_target2.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_expected_grids():
    """Load expected grid data from manual_grids.txt"""
    expected_grids = []
    current_grid = []
    
    with open('logs/analysis/manual_grids.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # Empty line indicates end of grid
                if current_grid and len(current_grid) == 9:
                    expected_grids.append(current_grid)
                current_grid = []
                continue
                
            # Split the line into cells and process each cell
            cells = line.split()
            row = []
            for cell in cells:
                if cell == '--':
                    row.append(None)
                else:
                    # Extract number and confidence using regex
                    match = re.match(r'(\d+)\((\d+)\)', cell)
                    if match:
                        number = int(match.group(1))
                        confidence = int(match.group(2))
                        row.append((number, confidence))
                    else:
                        row.append(None)
            
            if row:  # Only append non-empty rows
                current_grid.append(row)
    
    # Add the last grid if it exists
    if current_grid and len(current_grid) == 9:
        expected_grids.append(current_grid)
    
    logging.info(f"Loaded {len(expected_grids)} expected grids")
    return expected_grids

def test_number_reader():
    """Test the number reader on the enhanced images"""
    from read_number_from_image import NumberReader
    
    # Initialize the number reader
    reader = NumberReader()
    
    # Load expected grids
    expected_grids = load_expected_grids()
    
    # Process test images
    test_dir = Path('tests/png_v2')  # Use enhanced images
    results = []
    total_correct = 0
    total_cells = 0
    
    for png_file in sorted(test_dir.glob('*.png')):
        # Extract grid number from filename (sudoku1, sudoku2, etc.)
        grid_num = int(re.search(r'sudoku(\d+)', png_file.stem).group(1))
        logging.info(f"\nTesting grid {grid_num} from {png_file.name}")
        
        if grid_num > len(expected_grids):
            logging.warning(f"No expected data for grid {grid_num}")
            continue
            
        expected_grid = expected_grids[grid_num - 1]
        image = cv2.imread(str(png_file))
        
        # Calculate cell dimensions
        height, width = image.shape[:2]
        cell_height = height // 9
        cell_width = width // 9
        
        grid_results = []
        correct_cells = 0
        
        for i in range(9):
            for j in range(9):
                # Extract cell
                y1 = i * cell_height
                y2 = (i + 1) * cell_height
                x1 = j * cell_width
                x2 = (j + 1) * cell_width
                cell = image[y1:y2, x1:x2]
                
                # Read number
                number = reader.read_number(cell)
                
                # Compare with expected
                expected = expected_grid[i][j]
                if expected is not None:
                    expected_number = expected[0] if isinstance(expected, tuple) else expected
                    is_correct = number == expected_number
                    
                    if is_correct:
                        correct_cells += 1
                        logging.info(f"Cell ({i}, {j}): Correctly recognized {number}")
                    else:
                        logging.warning(f"Cell ({i}, {j}): Expected {expected_number}, got {number}")
                    
                    grid_results.append({
                        'position': (i, j),
                        'expected': expected_number,
                        'recognized': number,
                        'correct': is_correct
                    })
        
        total_cells += len(grid_results)
        total_correct += correct_cells
        accuracy = (correct_cells / len([x for row in expected_grid for x in row if x is not None])) * 100
        logging.info(f"Grid {grid_num} accuracy: {accuracy:.1f}% ({correct_cells}/{len([x for row in expected_grid for x in row if x is not None])})")
        
        results.append({
            'grid': grid_num,
            'accuracy': accuracy,
            'correct_cells': correct_cells,
            'total_cells': len([x for row in expected_grid for x in row if x is not None]),
            'results': grid_results
        })
    
    # Calculate and log overall accuracy
    overall_accuracy = (total_correct / total_cells) * 100 if total_cells > 0 else 0
    logging.info(f"\nOverall accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_cells})")
    
    # Save detailed results
    with open('test_results_v1_target2.json', 'w') as f:
        json.dump(results, f, indent=2)
    logging.info("Detailed results saved to test_results_v1_target2.json")

if __name__ == "__main__":
    test_number_reader() 