import cv2
import numpy as np
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_numbers.log'),
        logging.StreamHandler()
    ]
)

def parse_grid_file(file_path):
    """Parse the manual_grids.txt file to extract grid information."""
    grids = []
    current_grid = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('Grid'):
            if current_grid:
                grids.append(current_grid)
            current_grid = []
        elif '|' in line:
            # Extract numbers and their confidence levels
            cells = re.findall(r'(\d+[hlm]?|--)', line)
            current_grid.append(cells)
    
    if current_grid:
        grids.append(current_grid)
    
    return grids

def extract_number_images(grid_number, grid_data, png_dir, saved_numbers):
    """Extract number images from the specified grid."""
    # Find the corresponding PNG file
    png_files = list(png_dir.glob(f"*sudoku{grid_number}.png"))
    if not png_files:
        logging.error(f"No PNG file found for grid {grid_number}")
        return saved_numbers
    
    png_file = png_files[0]
    image = cv2.imread(str(png_file))
    if image is None:
        logging.error(f"Could not read image: {png_file}")
        return saved_numbers
    
    # Calculate cell dimensions
    height, width = image.shape[:2]
    cell_height = height // 9
    cell_width = width // 9
    
    # Process each cell in the grid
    for row in range(9):
        for col in range(9):
            cell = grid_data[row][col]
            if cell != '--':  # Skip empty cells
                # Extract the number and confidence level
                number = cell[0]
                confidence = cell[1] if len(cell) > 1 else 'h'
                
                # Skip if we already have this number
                if number in saved_numbers:
                    continue
                
                # Calculate cell boundaries
                y1 = row * cell_height
                y2 = (row + 1) * cell_height
                x1 = col * cell_width
                x2 = (col + 1) * cell_width
                
                # Extract cell with padding
                padding = int(min(cell_height, cell_width) * 0.15)  # 15% padding
                cell_image = image[y1+padding:y2-padding, x1+padding:x2-padding]
                
                # Create a white background image
                output_size = (64, 64)
                output_image = np.ones((output_size[0], output_size[1], 3), dtype=np.uint8) * 255
                
                # Resize the cell to fit in the output image
                cell_resized = cv2.resize(cell_image, (output_size[0] - 10, output_size[1] - 10))
                
                # Calculate position to center the number
                y_offset = (output_size[0] - cell_resized.shape[0]) // 2
                x_offset = (output_size[1] - cell_resized.shape[1]) // 2
                
                # Place the number in the center
                output_image[y_offset:y_offset+cell_resized.shape[0], 
                           x_offset:x_offset+cell_resized.shape[1]] = cell_resized
                
                # Save the number image
                output_path = Path("data") / f"{number}.png"
                cv2.imwrite(str(output_path), output_image)
                logging.info(f"Saved number {number} to {output_path}")
                saved_numbers.add(number)
    
    return saved_numbers

def main():
    # Read the manual grids file
    grid_file = Path("data/manual_grids.txt")
    if not grid_file.exists():
        logging.error(f"Grid file not found: {grid_file}")
        return
    
    # Parse the grid file
    grids = parse_grid_file(grid_file)
    logging.info(f"Found {len(grids)} grids in the file")
    
    # Get PNG directory
    png_dir = Path("logs/png")
    if not png_dir.exists():
        logging.error(f"PNG directory not found: {png_dir}")
        return
    
    # Keep track of saved numbers
    saved_numbers = set()
    
    # Process each grid
    for i, grid_data in enumerate(grids, 1):
        logging.info(f"\nProcessing grid {i}")
        saved_numbers = extract_number_images(i, grid_data, png_dir, saved_numbers)
        
        # If we have all numbers, we can stop
        if len(saved_numbers) == 9:
            logging.info("Found all numbers 1-9, stopping.")
            break
    
    logging.info("\nAll grids processed. Check the data directory for extracted number images.")

if __name__ == "__main__":
    main() 