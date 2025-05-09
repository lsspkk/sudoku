import cv2
import numpy as np
import logging
from pathlib import Path
import json
import os
import shutil
import argparse
from read_number_from_image import NumberReader
from PIL import Image
import pytesseract
from text_sudoku import format_sudoku_grid, add_confidence_levels

def cleanup_output():
    """Clean up previous output files and directories"""
    # Clean up analysis directory in logs
    analysis_dir = logs_dir / 'analysis'
    if analysis_dir.exists():
        shutil.rmtree(analysis_dir)
    analysis_dir.mkdir(exist_ok=True)
    
    # Clean up log files
    log_file = logs_dir / 'adjust_number_reading.log'
    if log_file.exists():
        log_file.unlink()

# Create output directories
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
analysis_dir = logs_dir / 'analysis'
analysis_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'adjust_number_reading.log'),
        logging.StreamHandler()
    ]
)

class SudokuCellAnalyzer:
    def __init__(self, image_path, grid_number):
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        self.height, self.width = self.image.shape[:2]
        self.cell_height = self.height // 9
        self.cell_width = self.width // 9
        self.grid_number = grid_number
        
        # Initialize number reader
        self.number_reader = NumberReader()
        
        # Log initial image and cell sizes
        logging.info(f"Image size: {self.width}x{self.height}")
        logging.info(f"Cell size: {self.cell_width}x{self.cell_height}")
        
    def analyze_cell(self, row, col):
        """Analyze a single cell and return its properties"""
        # Calculate cell boundaries
        y1 = row * self.cell_height
        y2 = (row + 1) * self.cell_height
        x1 = col * self.cell_width
        x2 = (col + 1) * self.cell_width
        
        # Extract cell with padding
        padding = int(min(self.cell_height, self.cell_width) * self.number_reader.settings["cell_padding"])
        cell = self.image[y1+padding:y2-padding, x1+padding:x2-padding]
        
        # Use NumberReader to analyze the cell
        result = self.number_reader.read_number(cell)
        
        # Add position and size information
        cell_info = {
            "position": (row, col),
            "size": (self.cell_height, self.cell_width),
            "padding": padding,
            "cell_center": (x1 + self.cell_width//2, y1 + self.cell_height//2),
            **result  # Include all the results from NumberReader
        }
        
        return cell_info, cell

    def analyze_grid(self):
        """Analyze the entire grid and save debug images"""
        grid_analysis = []
        recognized_grid = [['--' for _ in range(9)] for _ in range(9)]  # Initialize with '--'
        confidence_grid = [['F' for _ in range(9)] for _ in range(9)]  # Initialize with 'F'
        
        # Create debug image
        debug_image = self.image.copy()
        
        for row in range(9):
            for col in range(9):
                cell_info, cell = self.analyze_cell(row, col)
                grid_analysis.append(cell_info)
                
                # Store recognized number and confidence
                if cell_info["recognized_number"]:
                    recognized_grid[row][col] = cell_info["recognized_number"]
                    confidence_grid[row][col] = cell_info["confidence_level"][0]  # First letter of confidence level
                else:
                    # Keep '--' for empty cells
                    confidence_grid[row][col] = 'F'  # Failed recognition
                
                # Draw cell boundaries and center
                x1 = col * self.cell_width
                y1 = row * self.cell_height
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                
                # Draw cell rectangle
                cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
                
                # Draw cell center
                center_x = x1 + self.cell_width // 2
                center_y = y1 + self.cell_height // 2
                cv2.circle(debug_image, (center_x, center_y), 2, (0, 0, 255), -1)
                
                # Draw padding area
                padding = int(min(self.cell_height, self.cell_width) * self.number_reader.settings["cell_padding"])
                cv2.rectangle(debug_image, 
                            (x1 + padding, y1 + padding),
                            (x2 - padding, y2 - padding),
                            (255, 0, 0), 1)
                
                # Draw recognized number with confidence level
                if cell_info["recognized_number"]:
                    # Choose color based on confidence level
                    if cell_info["confidence_level"] == "high":
                        color = (0, 255, 0)  # Green for high confidence
                    elif cell_info["confidence_level"] == "medium":
                        color = (0, 165, 255)  # Orange for medium confidence
                    else:
                        color = (0, 0, 255)  # Red for low confidence
                    
                    cv2.putText(debug_image, 
                              f"{cell_info['recognized_number']}",
                              (center_x - 5, center_y + 5),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              0.5,
                              color,
                              1)
        
        # Save debug image with grid number
        cv2.imwrite(str(analysis_dir / f'grid_analysis{self.grid_number}.png'), debug_image)
        
        return {
            'grid_analysis': grid_analysis,
            'recognized_grid': recognized_grid,
            'confidence_grid': confidence_grid
        }

    def save_analysis(self, grid_analysis):
        """Save analysis results to log file"""
        analysis_data = {
            "grid_number": self.grid_number,
            "image_size": (self.width, self.height),
            "cell_size": (self.cell_width, self.cell_height),
            "settings": self.number_reader.settings,
            "grid_analysis": grid_analysis['grid_analysis']
        }
        
        # Save detailed analysis to JSON
        with open(analysis_dir / f'detailed_analysis{self.grid_number}.json', 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Log summary
        logging.info(f"Image size: {self.width}x{self.height}")
        logging.info(f"Cell size: {self.cell_width}x{self.cell_height}")
        logging.info(f"Cell padding: {self.number_reader.settings['cell_padding']}")
        logging.info(f"Cells with content: {sum(1 for cell in grid_analysis['grid_analysis'] if cell['has_content'])}")
        
        # Count confidence levels
        confidence_counts = {"high": 0, "medium": 0, "low": 0, "failed": 0}
        for cell in grid_analysis['grid_analysis']:
            if cell['has_content']:
                confidence_counts[cell['confidence_level']] += 1
        
        logging.info("\nConfidence Level Summary:")
        logging.info(f"High confidence: {confidence_counts['high']} cells")
        logging.info(f"Medium confidence: {confidence_counts['medium']} cells")
        logging.info(f"Low confidence: {confidence_counts['low']} cells")
        logging.info(f"Failed recognition: {confidence_counts['failed']} cells")
        
        # Log recognition results
        logging.info("\nDetailed Recognition Results:")
        for cell in grid_analysis['grid_analysis']:
            if cell['has_content']:
                if cell['recognized_number']:
                    logging.info(f"Cell at {cell['position']}: Recognized as {cell['recognized_number']} "
                               f"(confidence: {cell['confidence']:.1f}%, level: {cell['confidence_level']})")
                    if len(cell['all_matches']) > 1:
                        logging.info(f"  Alternative matches: {cell['all_matches']}")
                else:
                    logging.warning(f"Cell at {cell['position']}: Failed to recognize number")
            if cell['has_content'] and cell['contour_count'] > 1:
                logging.warning(f"Cell at {cell['position']} has multiple contours: {cell['contour_count']}")
        
        return grid_analysis['recognized_grid'], grid_analysis['confidence_grid']

def save_consolidated_grids(all_grids, all_confidence_grids):
    """Save all recognized grids to a single file"""
    with open(analysis_dir / 'recognized_grids.txt', 'w') as f:
        f.write("Recognized Sudoku Grids\n")
        f.write("=" * 50 + "\n\n")
        
        for grid_num, (grid, conf_grid) in enumerate(zip(all_grids, all_confidence_grids), 1):
            f.write(f"Grid {grid_num}:\n")
            
            # Format grid with confidence levels using cell_width=2
            formatted_grid = add_confidence_levels(grid, conf_grid, cell_width=2)
            f.write(formatted_grid)
            f.write("\n\n")
            
            # Add confidence level legend
            f.write("Confidence Levels:\n")
            f.write("H = High confidence\n")
            f.write("M = Medium confidence\n")
            f.write("L = Low confidence\n")
            f.write("F = Failed recognition\n")
            f.write("\n" + "=" * 50 + "\n\n")

def analyze_image(image_path, output_dir, grid_number):
    """Analyze a single image and save results."""
    # ... existing code until grid creation ...

    # Create confidence grid
    confidence_grid = [[' ' for _ in range(9)] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if grid[i][j]:
                conf = confidence_levels[i][j]
                if conf >= 0.8:
                    confidence_grid[i][j] = 'H'
                elif conf >= 0.6:
                    confidence_grid[i][j] = 'M'
                else:
                    confidence_grid[i][j] = 'L'
            else:
                confidence_grid[i][j] = 'F'

    # Save detailed analysis
    analysis_data = {
        'grid': grid,
        'confidence_levels': confidence_levels,
        'confidence_grid': confidence_grid,
        'image_size': image.shape[:2],
        'cell_size': cell_size,
        'cell_padding': cell_padding,
        'cells_with_content': sum(1 for row in grid for cell in row if cell)
    }
    
    analysis_file = output_dir / f'detailed_analysis{grid_number}.json'
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)

    # Save visual analysis
    analysis_image = image.copy()
    for i in range(9):
        for j in range(9):
            if grid[i][j]:
                x, y = j * cell_size, i * cell_size
                cv2.rectangle(analysis_image, (x, y), (x + cell_size, y + cell_size), (0, 255, 0), 2)
                cv2.putText(analysis_image, str(grid[i][j]), (x + 10, y + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    analysis_image_path = output_dir / f'grid_analysis{grid_number}.png'
    cv2.imwrite(str(analysis_image_path), analysis_image)

    # Format and save grid with confidence levels
    formatted_grid = add_confidence_levels(grid, confidence_grid)
    with open(output_dir / 'recognized_grids.txt', 'a') as f:
        f.write(f"\nGrid {grid_number}:\n")
        f.write(formatted_grid)
        f.write("\n\n")

    return grid, confidence_levels

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze Sudoku grid images')
    parser.add_argument('--cleanup', action='store_true', help='Clean up previous output before starting')
    parser.add_argument('--max-images', type=int, default=1, help='Maximum number of images to analyze')
    args = parser.parse_args()
    
    # Clean up if requested
    if args.cleanup:
        cleanup_output()
        logging.info("Cleaned up previous output files")
    
    # Get list of PNG files from logs/png directory
    png_dir = logs_dir / "png"
    if not png_dir.exists():
        logging.error(f"PNG directory not found: {png_dir}")
        return
    
    png_files = sorted(list(png_dir.glob("*.png")))
    if not png_files:
        logging.error("No PNG files found in logs/png directory")
        return
    
    # Limit number of files to process
    png_files = png_files[:args.max_images]
    logging.info(f"Found {len(png_files)} PNG files to analyze")
    
    all_recognized_grids = []
    all_confidence_grids = []
    
    for idx, png_file in enumerate(png_files, 1):
        try:
            logging.info(f"\nAnalyzing {png_file.name}")
            
            analyzer = SudokuCellAnalyzer(png_file, idx)
            grid_analysis = analyzer.analyze_grid()
            recognized_grid, confidence_grid = analyzer.save_analysis(grid_analysis)
            
            all_recognized_grids.append(recognized_grid)
            all_confidence_grids.append(confidence_grid)
            
            logging.info(f"Analysis complete for {png_file.name}")
            
        except Exception as e:
            logging.error(f"Error analyzing {png_file.name}: {str(e)}")
    
    # Save consolidated grids
    save_consolidated_grids(all_recognized_grids, all_confidence_grids)
    
    logging.info("\nAll analyses complete. Check logs/analysis/ for results:")
    logging.info("- grid_analysisN.png: Visual representation of each grid")
    logging.info("- detailed_analysisN.json: Complete analysis data for each grid")
    logging.info("- recognized_grids.txt: All recognized numbers and confidence levels")

if __name__ == "__main__":
    main() 