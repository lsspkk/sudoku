#!/usr/bin/env python
import os
import sys
import argparse
import logging
import json
import traceback
from pathlib import Path
import cv2
import numpy as np
import yaml

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the cell extractor
from src.cell_extract import CellExtractor

# Add a simple logger that prints to console and writes to a log file
class SimpleLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        # Clear the log file at start
        with open(self.log_path, 'w') as f:
            f.write('')

    def log(self, level, msg):
        line = f"{level}: {msg}"
        print(line)
        with open(self.log_path, 'a') as f:
            f.write(line + '\n')

    def info(self, msg):
        self.log('INFO', msg)

    def error(self, msg):
        self.log('ERROR', msg)

    def debug(self, msg):
        self.log('DEBUG', msg)

    def warning(self, msg):
        self.log('WARNING', msg)

class PNGGridExtractor:
    def __init__(self, input_dir="logs/png", output_dir="logs/analysis", clean=False, limit_grids=None, config_path="src/config.yaml", debug=False):
        """
        Initialize the PNG grid extractor.
        
        Args:
            input_dir: Directory containing PNG files
            output_dir: Directory to save the extraction results
            clean: Whether to clean the output directory before extraction
            limit_grids: Maximum number of grids to extract (None for all grids)
            config_path: Path to the OCR settings configuration file
            debug: Whether to enable debug output
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.clean = clean
        self.limit_grids = limit_grids
        self.config_path = config_path
        self.debug = debug
        
        # Setup simple logger
        self.logger = SimpleLogger(os.path.join('logs', 'png_grid_extractor.log'))
        self.logger.info("Logger initialized for PNGGridExtractor")
        
        # Ensure output directories exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join('logs', 'debug'), exist_ok=True)
        # Clean debug directory if requested
        if self.clean:
            debug_dir = os.path.join('logs', 'debug')
            self.logger.info(f"Cleaning debug directory: {debug_dir}")
            for file in os.listdir(debug_dir):
                path = os.path.join(debug_dir, file)
                if os.path.isfile(path):
                    os.remove(path)
        
        try:
            # Initialize the cell extractor
            self.logger.info(f"Initializing CellExtractor with config: {config_path}")
            self.cell_extractor = CellExtractor(config_path=config_path)
            self.logger.info("CellExtractor initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing CellExtractor: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def scan_for_png_files(self):
        """
        Scan the input directory for PNG files, sorted by page number.
        Returns:
            List of paths to PNG files
        """
        self.logger.info(f"Scanning for PNG files in {self.input_dir}")

        if not os.path.exists(self.input_dir):
            self.logger.error(f"Input directory not found: {self.input_dir}")
            return []

        def extract_page_number(filename):
            import re
            match = re.search(r'_page(\d+)', filename)
            return int(match.group(1)) if match else float('inf')

        png_files = [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith('.png')
        ]
        # Sort by (page number, filename) to ensure stable order
        png_files.sort(key=lambda f: (extract_page_number(f), os.path.basename(f)))

        self.logger.info(f"Found {len(png_files)} PNG files")
        for png_file in png_files:
            self.logger.debug(f"  {png_file}")

        return png_files
    
    def detect_grid(self, image):
        """
        Detect a Sudoku grid in the image.
        
        Args:
            image: The source image as numpy array
            
        Returns:
            A 9x9 array of cell coordinates (x, y, width, height),
            or None if no grid is detected
        """
        self.logger.info("Detecting grid in image")
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour (which should be the grid)
        max_area = 0
        grid_contour = None
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                grid_contour = contour
        
        if grid_contour is None:
            self.logger.error("No grid detected")
            return None
        
        # Get the bounding rectangle of the grid
        x, y, w, h = cv2.boundingRect(grid_contour)
        
        # Check if it's approximately square
        aspect_ratio = w / h
        if aspect_ratio < 0.7 or aspect_ratio > 1.3:
            self.logger.warning(f"Grid has unusual aspect ratio: {aspect_ratio}")
        
        # Create a 9x9 grid of cells
        cells = []
        cell_width = w // 9
        cell_height = h // 9
        
        for row in range(9):
            cell_row = []
            for col in range(9):
                cell_x = x + col * cell_width
                cell_y = y + row * cell_height
                cell_row.append((cell_x, cell_y, cell_width, cell_height))
            cells.append(cell_row)
        
        self.logger.info(f"Grid detected: {w}x{h} at ({x}, {y})")
        return cells
    
    def extract_grid_numbers(self, image, grid_cells):
        """
        Extract numbers from the grid cells.
        
        Args:
            image: The source image as numpy array
            grid_cells: A 9x9 array of cell coordinates (x, y, width, height)
            
        Returns:
            - A 9x9 array of extracted numbers (None for empty cells)
            - A 9x9 array of confidence scores (None for empty cells)
        """
        self.logger.info("Extracting numbers from grid cells")
        
        grid_numbers = []
        confidence_scores = []
        
        for row in range(9):
            number_row = []
            confidence_row = []
            
            for col in range(9):
                x, y, w, h = grid_cells[row][col]
                
                # Extract and analyze the cell
                result = self.cell_extractor.extract_cell(image, x, y, w, h)
                
                number_row.append(result['number'])
                confidence_row.append(result['confidence'])
                
                self.logger.debug(f"Cell ({row}, {col}): {result['number']} with confidence {result['confidence']}")
            
            grid_numbers.append(number_row)
            confidence_scores.append(confidence_row)
        
        return grid_numbers, confidence_scores
    
    def save_grid_to_file(self, grid, confidence, grid_number, output_file):
        """
        Save the extracted grid to a text file.
        
        Args:
            grid: A 9x9 array of extracted numbers (None for empty cells)
            confidence: A 9x9 array of confidence scores (None for empty cells)
            grid_number: The grid number
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Saving grid {grid_number} to {output_file}")
        
        # Get confidence threshold values
        high_threshold = self.cell_extractor.config['confidence_thresholds']['high']
        medium_threshold = self.cell_extractor.config['confidence_thresholds']['medium']
        low_threshold = self.cell_extractor.config['confidence_thresholds']['low']
        
        try:
            # Check if the file exists
            file_exists = os.path.exists(output_file)
            
            # Open the file in append mode if it exists, otherwise create it
            mode = 'a' if file_exists else 'w'
            
            with open(output_file, mode) as f:
                if file_exists:
                    f.write("\n\n")  # Add space between grids
                
                # Write the grid header
                f.write(f"Grid {grid_number}:\n")
                
                # Write the grid
                f.write("+-------+-------+-------+\n")
                
                for i, row in enumerate(grid):
                    f.write("| ")
                    
                    for j, cell in enumerate(row):
                        if cell is None:
                            f.write("- ")
                        else:
                            conf = confidence[i][j]
                            if conf >= high_threshold:
                                f.write(f"{cell} ")
                            elif conf >= medium_threshold:
                                f.write(f"{cell} ")
                            else:
                                f.write(f"{cell} ")
                        
                        # Add cell separators
                        if j % 3 == 2 and j < 8:
                            f.write("| ")
                    
                    f.write("|\n")
                    
                    # Add row separators
                    if i % 3 == 2 and i < 8:
                        f.write("+-------+-------+-------+\n")
                
                # Write the bottom border
                f.write("+-------+-------+-------+\n")
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving grid to file: {e}")
            return False
    
    def save_grid_analysis(self, grid, confidence, grid_number, output_file):
        """
        Save detailed grid analysis to a text file.
        
        Args:
            grid: A 9x9 array of extracted numbers (None for empty cells)
            confidence: A 9x9 array of confidence scores (None for empty cells)
            grid_number: The grid number
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Saving grid analysis for grid {grid_number} to {output_file}")
        
        # Get confidence threshold values
        high_threshold = self.cell_extractor.config['confidence_thresholds']['high']
        medium_threshold = self.cell_extractor.config['confidence_thresholds']['medium']
        
        try:
            # Check if the file exists
            file_exists = os.path.exists(output_file)
            
            # Open the file in append mode if it exists, otherwise create it
            mode = 'a' if file_exists else 'w'
            
            with open(output_file, mode) as f:
                if file_exists:
                    f.write("\n\n")  # Add space between grids
                
                # Write the grid header
                f.write(f"Grid {grid_number}:\n")
                
                # Write the grid with confidence indicators
                f.write("+----------+----------+----------+\n")
                
                for i, row in enumerate(grid):
                    f.write("| ")
                    
                    for j, cell in enumerate(row):
                        if cell is None:
                            f.write("-- ")
                        else:
                            conf = confidence[i][j]
                            if conf >= high_threshold:
                                f.write(f"{cell}h ")
                            elif conf >= medium_threshold:
                                f.write(f"{cell}m ")
                            else:
                                f.write(f"{cell}l ")
                        
                        # Add cell separators
                        if j % 3 == 2 and j < 8:
                            f.write("| ")
                    
                    f.write("|\n")
                    
                    # Add row separators
                    if i % 3 == 2 and i < 8:
                        f.write("+----------+----------+----------+\n")
                
                # Write the bottom border
                f.write("+----------+----------+----------+\n")
                
                # Write the confidence level legend
                f.write("\nConfidence Levels:\n")
                f.write(f"h = High confidence (>={high_threshold}%)\n")
                f.write(f"m = Medium confidence (>={medium_threshold}%)\n")
                f.write(f"l = Low confidence (<{medium_threshold}%)")
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving grid analysis to file: {e}")
            return False
    
    def save_grid_json(self, grid, confidence, grid_number, source_file, output_file):
        """
        Save the grid data as JSON.
        
        Args:
            grid: A 9x9 array of extracted numbers (None for empty cells)
            confidence: A 9x9 array of confidence scores (None for empty cells)
            grid_number: The grid number
            source_file: Path to the source PNG file
            output_file: Path to the output JSON file
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Saving grid JSON for grid {grid_number} to {output_file}")
        
        # Create the JSON data
        data = {
            "grid_number": grid_number,
            "source_file": source_file,
            "cells": [],
            "statistics": {
                "total_cells": 0,
                "recognized_cells": 0,
                "average_confidence": 0
            }
        }
        
        # Add cells
        total_confidence = 0
        recognized_cells = 0
        
        for i in range(9):
            for j in range(9):
                cell = {
                    "position": [i, j],
                    "number": grid[i][j],
                    "confidence": confidence[i][j]
                }
                
                data["cells"].append(cell)
                
                if grid[i][j] is not None:
                    recognized_cells += 1
                    total_confidence += confidence[i][j]
        
        # Update statistics
        data["statistics"]["total_cells"] = 81
        data["statistics"]["recognized_cells"] = recognized_cells
        
        if recognized_cells > 0:
            data["statistics"]["average_confidence"] = total_confidence / recognized_cells
        
        try:
            # Write the JSON data to the output file
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving grid JSON to file: {e}")
            return False
    
    def process_png_files(self):
        """
        Process PNG files and extract Sudoku grids.
        Returns:
            List of processed PNG files
        """
        try:
            # Clean the output directory if requested
            if self.clean and os.path.exists(self.output_dir):
                self.logger.info(f"Cleaning output directory: {self.output_dir}")
                for file in os.listdir(self.output_dir):
                    path = os.path.join(self.output_dir, file)
                    if os.path.isfile(path):
                        os.remove(path)
            # Clean grids.txt if requested
            main_output_file = os.path.join('logs', 'grids.txt')
            if self.clean and os.path.exists(main_output_file):
                self.logger.info(f"Cleaning {main_output_file}")
                with open(main_output_file, 'w') as f:
                    f.write("")

            # Scan for PNG files
            png_files = self.scan_for_png_files()
            if not png_files:
                self.logger.error("No PNG files found")
                return []
            # Apply grid limit if specified
            if self.limit_grids is not None and len(png_files) > self.limit_grids:
                self.logger.info(f"Limiting to {self.limit_grids} grids")
                png_files = png_files[:self.limit_grids]
            # Process the PNG files
            processed_files = []
            grid_number = 0
            analysis_output_file = os.path.join(self.output_dir, 'grids_analysis.txt')
            grid1_debug_lines = []
            for png_file in png_files:
                self.logger.info(f"Processing {png_file}")
                try:
                    # Load the image
                    self.logger.debug(f"Loading image: {png_file}")
                    image = cv2.imread(png_file)
                    if image is None:
                        self.logger.error(f"Failed to load image: {png_file}")
                        continue
                    self.logger.debug(f"Image loaded, shape: {image.shape}")
                    # Save debug image if debug is enabled
                    if self.debug:
                        debug_image_path = os.path.join('logs', 'debug', f"debug_input_{os.path.basename(png_file)}")
                        cv2.imwrite(debug_image_path, image)
                        self.logger.debug(f"Saved debug input image to {debug_image_path}")
                    # Detect the grid
                    self.logger.debug("Detecting grid...")
                    grid_cells = self.detect_grid(image)
                    if grid_cells is None:
                        self.logger.error(f"No grid detected in {png_file}")
                        continue
                    self.logger.debug(f"Grid detected, cells: {len(grid_cells)}x{len(grid_cells[0])}")
                    # Extract numbers from the grid
                    self.logger.debug("Extracting numbers from grid...")
                    extract_cell_calls = 0
                    grid_numbers = []
                    confidence_scores = []
                    cell_results = []
                    for row in range(9):
                        number_row = []
                        confidence_row = []
                        for col in range(9):
                            x, y, w, h = grid_cells[row][col]
                            extract_cell_calls += 1
                            self.logger.info(f"Calling extract_cell for grid={grid_number+1}, row={row}, col={col}, x={x}, y={y}, w={w}, h={h}")
                            result = self.cell_extractor.extract_cell(image, x, y, w, h, grid_number=grid_number+1, row=row, col=col)
                            number_row.append(result['number'])
                            confidence_row.append(result['confidence'])
                            cell_results.append({
                                'row': row, 'col': col, 'x': x, 'y': y, 'w': w, 'h': h,
                                'number': result['number'], 'confidence': result['confidence'],
                                'confidence_level': result['confidence_level'], 'has_content': result['has_content']
                            })
                            if grid_number == 0:  # grid_number is incremented after this loop, so 0 means grid 1
                                debug_img_path = os.path.join('logs', 'debug', f"grid1_{row}_{col}_preprocessed.png")
                                grid1_debug_lines.append(f"Cell ({row},{col}) at ({x},{y},{w},{h}): debug_img='{debug_img_path}'\n")
                        grid_numbers.append(number_row)
                        confidence_scores.append(confidence_row)
                    grid_number += 1
                    self.logger.info(f"Grid {grid_number}: {png_file}, image shape: {image.shape}, extract_cell calls: {extract_cell_calls}")
                    for cell in cell_results:
                        self.logger.info(f"  Cell ({cell['row']},{cell['col']}) at ({cell['x']},{cell['y']},{cell['w']},{cell['h']}): number={cell['number']} confidence={cell['confidence']} level={cell['confidence_level']} has_content={cell['has_content']}")
                    # Save the grid to the main output file
                    self.logger.debug(f"Saving grid to file: {main_output_file}")
                    if not self.save_grid_to_file(grid_numbers, confidence_scores, grid_number, main_output_file):
                        self.logger.error(f"Failed to save grid to file: {main_output_file}")
                    # Save the grid analysis
                    self.logger.debug(f"Saving grid analysis to file: {analysis_output_file}")
                    if not self.save_grid_analysis(grid_numbers, confidence_scores, grid_number, analysis_output_file):
                        self.logger.error(f"Failed to save grid analysis to file: {analysis_output_file}")
                    # Save the grid JSON
                    json_output_file = os.path.join(self.output_dir, f"grid{grid_number}.json")
                    self.logger.debug(f"Saving grid JSON to file: {json_output_file}")
                    if not self.save_grid_json(grid_numbers, confidence_scores, grid_number, png_file, json_output_file):
                        self.logger.error(f"Failed to save grid JSON to file: {json_output_file}")
                    processed_files.append(png_file)
                    self.logger.info(f"Successfully processed {png_file}")
                except Exception as e:
                    self.logger.error(f"Error processing {png_file}: {e}")
                    self.logger.error(traceback.format_exc())
            if grid_number == 1 and grid1_debug_lines:
                with open(os.path.join('logs', 'debug', 'grid1_cell_extract.py'), 'w') as f:
                    f.writelines(grid1_debug_lines)
            self.logger.info(f"Processed {len(processed_files)} out of {len(png_files)} PNG files")
            return processed_files
        except Exception as e:
            self.logger.error(f"Error in process_png_files: {e}")
            self.logger.error(traceback.format_exc())
            return []


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Extract Sudoku grids from PNG files')
    parser.add_argument('--input_dir', default='logs/png', help='Directory containing PNG files')
    parser.add_argument('--output_dir', default='logs/analysis', help='Directory to save the extraction results')
    parser.add_argument('--clean', action='store_true', help='Clean the output directory before extraction')
    parser.add_argument('--limit_grids', type=int, help='Maximum number of grids to extract')
    parser.add_argument('--config', default='src/config.yaml', help='Path to the OCR settings configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    try:
        extractor = PNGGridExtractor(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            clean=args.clean,
            limit_grids=args.limit_grids,
            config_path=args.config,
            debug=args.debug
        )
        
        processed_files = extractor.process_png_files()
        
        if processed_files:
            print(f"Processed {len(processed_files)} PNG files")
            for processed_file in processed_files:
                print(f"  {processed_file}")
            return 0
        else:
            print("No PNG files processed")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main()) 