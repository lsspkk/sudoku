import cv2
import numpy as np
from pathlib import Path
import logging
import json
import sys
import os
import re

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from read_number_from_image_v2 import NumberReaderV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_number_reader_v2.log'),
        logging.StreamHandler()
    ]
)

def load_expected_grids():
    """Load expected grid data from manual_grids.txt."""
    grids = []
    current_grid = []
    
    with open(Path("data/manual_grids.txt"), 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('Grid'):
            if current_grid:
                if len(current_grid) == 9 and all(len(row) == 9 for row in current_grid):
                    grids.append(current_grid)
            current_grid = []
        elif '|' in line and not line.startswith('+'):
            # Extract numbers and their confidence levels
            row = []
            cells = line.split('|')[1:-1]  # Skip first and last |
            for cell in cells:
                parts = cell.strip().split()
                for part in parts:
                    if part == '--':
                        row.append(None)
                    else:
                        # Extract number and confidence using regex
                        match = re.match(r'(\d+)([hlm])?', part)
                        if match:
                            number, confidence = match.groups()
                            confidence = confidence if confidence else 'h'
                            row.append((number, confidence))
                        else:
                            row.append(None)
            if row:  # Only append non-empty rows
                current_grid.append(row)
    
    if current_grid and len(current_grid) == 9 and all(len(row) == 9 for row in current_grid):
        grids.append(current_grid)
    
    return grids

def test_number_reader():
    """Test the number reader on all grids."""
    # Initialize number reader
    reader = NumberReaderV2()
    
    # Load expected grids
    expected_grids = load_expected_grids()
    logging.info(f"Loaded {len(expected_grids)} expected grids")
    
    # Get test images
    png_dir = Path("tests/png")
    png_files = sorted(list(png_dir.glob("*.png")))
    
    results = []
    
    for grid_idx, png_file in enumerate(png_files):
        if grid_idx >= len(expected_grids):
            logging.warning(f"No expected data for grid {grid_idx + 1}")
            break
            
        logging.info(f"\nTesting grid {grid_idx + 1} from {png_file.name}")
        
        # Read the image
        image = cv2.imread(str(png_file))
        if image is None:
            logging.error(f"Could not read image: {png_file}")
            continue
        
        # Calculate cell dimensions
        height, width = image.shape[:2]
        cell_height = height // 9
        cell_width = width // 9
        
        grid_results = []
        correct_count = 0
        total_cells = 0
        
        # Process each cell
        for row in range(9):
            for col in range(9):
                # Calculate cell boundaries
                y1 = row * cell_height
                y2 = (row + 1) * cell_height
                x1 = col * cell_width
                x2 = (col + 1) * cell_width
                
                # Extract cell with padding
                padding = int(min(cell_height, cell_width) * reader.settings["cell_padding"])
                cell = image[y1+padding:y2-padding, x1+padding:x2-padding]
                
                # Get expected number
                expected = expected_grids[grid_idx][row][col]
                
                # Skip empty cells
                if expected is None:
                    continue
                
                expected_number, expected_confidence = expected
                
                # Read number from cell
                result = reader.read_number(cell)
                
                # Compare with expected
                is_correct = (result["recognized_number"] == expected_number if result["has_content"] else False)
                if is_correct:
                    correct_count += 1
                total_cells += 1
                
                # Store result
                cell_result = {
                    "position": (row, col),
                    "expected": expected_number,
                    "expected_confidence": expected_confidence,
                    "recognized": result["recognized_number"],
                    "confidence": result["confidence"],
                    "confidence_level": result["confidence_level"],
                    "method": result["method"],
                    "is_correct": is_correct
                }
                grid_results.append(cell_result)
                
                # Log result
                if is_correct:
                    logging.info(f"Cell ({row}, {col}): Correctly recognized {expected_number}")
                else:
                    logging.warning(f"Cell ({row}, {col}): Expected {expected_number}, got {result['recognized_number']}")
        
        # Calculate accuracy
        accuracy = (correct_count / total_cells) * 100 if total_cells > 0 else 0
        
        # Store grid results
        grid_summary = {
            "grid_number": grid_idx + 1,
            "image_file": png_file.name,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_cells": total_cells,
            "cell_results": grid_results
        }
        results.append(grid_summary)
        
        logging.info(f"Grid {grid_idx + 1} accuracy: {accuracy:.1f}% ({correct_count}/{total_cells})")
    
    # Save detailed results
    with open('test_results_v2.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Calculate overall accuracy
    total_correct = sum(r["correct_count"] for r in results)
    total_cells = sum(r["total_cells"] for r in results)
    overall_accuracy = (total_correct / total_cells) * 100 if total_cells > 0 else 0
    
    logging.info(f"\nOverall accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_cells})")
    logging.info("Detailed results saved to test_results_v2.json")

if __name__ == "__main__":
    test_number_reader() 