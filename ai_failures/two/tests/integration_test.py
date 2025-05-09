#!/usr/bin/env python
import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
import difflib
import re

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IntegrationTester:
    def __init__(self, pdf_dir="pdf", logs_dir="logs", verbose=False):
        self.pdf_dir = pdf_dir
        self.logs_dir = logs_dir
        self.verbose = verbose
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, 'integration_test.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('integration_test')
        
        # Ensure directories exist
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(os.path.join(logs_dir, 'png'), exist_ok=True)
        os.makedirs(os.path.join(logs_dir, 'analysis'), exist_ok=True)
        
    def find_matching_pairs(self):
        """Find PDF files with matching TXT files in the pdf directory."""
        self.logger.info(f"Scanning {self.pdf_dir} for PDF/TXT pairs")
        
        pdf_files = [f for f in os.listdir(self.pdf_dir) if f.endswith('.pdf')]
        self.logger.debug(f"Found {len(pdf_files)} PDF files")
        
        matching_pairs = []
        for pdf_file in pdf_files:
            txt_file = pdf_file.replace('.pdf', '.txt')
            txt_path = os.path.join(self.pdf_dir, txt_file)
            
            if os.path.exists(txt_path):
                matching_pairs.append((pdf_file, txt_file))
        
        self.logger.info(f"Found {len(matching_pairs)} matching PDF/TXT pairs")
        return matching_pairs
    
    def run_extraction_pipeline(self, pdf_file):
        """Run the PDF to grid extraction pipeline for the given PDF file."""
        pdf_path = os.path.join(self.pdf_dir, pdf_file)
        self.logger.info(f"Processing {pdf_path}")
        
        # Step 1: Convert PDF to PNG
        self.logger.debug("Running pdf_grid_extractor.py")
        try:
            subprocess.run(
                ["python", "src/pdf_grid_extractor.py", "--input", pdf_path, "--clean"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running pdf_grid_extractor.py: {e}")
            return False
        
        # Step 2: Extract grids from PNG files
        self.logger.debug("Running png_grid_extractor.py")
        try:
            subprocess.run(
                ["python", "src/png_grid_extractor.py", "--clean"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running png_grid_extractor.py: {e}")
            return False
        
        return True
    
    def read_grid_file(self, file_path):
        """
        Read a grid file and return a list of grids.
        Each grid is a list of rows, where each row is a list of cell values.
        """
        grids = []
        current_grid = []
        
        with open(file_path, 'r') as f:
            grid_started = False
            for line in f:
                line = line.strip()
                
                # Check for grid header
                if line.startswith('Grid'):
                    if grid_started and current_grid:
                        grids.append(current_grid)
                        current_grid = []
                    grid_started = True
                    continue
                
                # Skip separator lines
                if '+' in line:
                    continue
                
                # Process grid rows
                if grid_started and '|' in line:
                    # Extract cell values from the row
                    cells = []
                    # Split by | and remove borders
                    parts = line.split('|')
                    for part in parts[1:-1]:  # Skip first and last elements (borders)
                        # Process each cell in the 3x3 section
                        for cell in part.strip().split():
                            cells.append(cell)
                    
                    current_grid.append(cells)
            
            # Add the last grid if there is one
            if grid_started and current_grid:
                grids.append(current_grid)
        
        return grids
    
    def compare_grids(self, expected_grid, actual_grid):
        """Compare two grids and return a list of differences."""
        differences = []
        
        for i in range(len(expected_grid)):
            for j in range(len(expected_grid[i])):
                if i < len(actual_grid) and j < len(actual_grid[i]):
                    if expected_grid[i][j] != actual_grid[i][j]:
                        differences.append((i, j, expected_grid[i][j], actual_grid[i][j]))
                else:
                    differences.append((i, j, expected_grid[i][j], "missing"))
        
        return differences
    
    def format_grid_for_display(self, grid, differences=None):
        """Format a grid for display, with optional marking of differences."""
        if differences is None:
            differences = []
        
        # Convert differences to a set of (row, col) tuples for quick lookup
        diff_positions = {(row, col) for row, col, _, _ in differences}
        
        formatted_rows = []
        
        # Add header row
        formatted_rows.append("+-------+-------+-------+")
        
        for i in range(9):
            row = []
            row.append("| ")
            
            for j in range(9):
                value = grid[i][j] if i < len(grid) and j < len(grid[i]) else "-"
                
                # Mark differences with an exclamation mark
                if (i, j) in diff_positions:
                    value = f"!{value}"
                
                row.append(value)
                
                # Add section separators
                if j % 3 == 2 and j < 8:
                    row.append(" | ")
                else:
                    row.append(" ")
            
            row.append("|")
            formatted_rows.append("".join(row))
            
            # Add horizontal separators
            if i % 3 == 2 and i < 8:
                formatted_rows.append("+-------+-------+-------+")
        
        # Add footer row
        formatted_rows.append("+-------+-------+-------+")
        
        return formatted_rows
    
    def compare_and_report(self, expected_file, actual_file):
        """Compare expected and actual grid files and generate a report."""
        self.logger.info(f"Comparing {expected_file} with {actual_file}")
        
        expected_grids = self.read_grid_file(expected_file)
        actual_grids = self.read_grid_file(actual_file)
        
        # Check if grids were read successfully
        if not expected_grids:
            self.logger.error(f"No grids found in {expected_file}")
            return False
        
        if not actual_grids:
            self.logger.error(f"No grids found in {actual_file}")
            return False
        
        # Compare the grids
        print(f"\nTesting: {os.path.basename(expected_file)}")
        print("=" * 40)
        
        total_differences = 0
        
        for i, (expected, actual) in enumerate(zip(expected_grids, actual_grids)):
            differences = self.compare_grids(expected, actual)
            total_differences += len(differences)
            
            print(f"Grid {i+1}:")
            expected_formatted = self.format_grid_for_display(expected)
            actual_formatted = self.format_grid_for_display(actual, differences)
            
            # Display side-by-side comparison
            print("Expected:                    Actual:")
            for e_line, a_line in zip(expected_formatted, actual_formatted):
                print(f"{e_line}    {a_line}")
            
            print(f"\nDifferences found: {len(differences)}")
            print("=" * 40)
        
        if len(expected_grids) != len(actual_grids):
            print(f"Warning: Found {len(expected_grids)} expected grids but {len(actual_grids)} actual grids")
        
        return total_differences == 0
    
    def run_tests(self):
        """Run tests for all matching PDF/TXT pairs."""
        pairs = self.find_matching_pairs()
        
        if not pairs:
            self.logger.error("No matching PDF/TXT pairs found")
            return False
        
        success = True
        
        for pdf_file, txt_file in pairs:
            # Run extraction pipeline
            if not self.run_extraction_pipeline(pdf_file):
                self.logger.error(f"Failed to process {pdf_file}")
                success = False
                continue
            
            # Compare expected vs actual grids
            expected_file = os.path.join(self.pdf_dir, txt_file)
            actual_file = os.path.join(self.logs_dir, "grids.txt")
            
            if not os.path.exists(actual_file):
                self.logger.error(f"Output file {actual_file} not found")
                success = False
                continue
            
            # Compare and report results
            result = self.compare_and_report(expected_file, actual_file)
            success = success and result
        
        return success


def main():
    parser = argparse.ArgumentParser(description='Run integration tests for the Sudoku extraction pipeline')
    parser.add_argument('--pdf_dir', default='pdf', help='Directory containing PDF files')
    parser.add_argument('--logs_dir', default='logs', help='Directory for log files')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = IntegrationTester(args.pdf_dir, args.logs_dir, args.verbose)
    success = tester.run_tests()
    
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed. See logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 