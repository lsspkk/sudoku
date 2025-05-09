#!/usr/bin/env python
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import cv2

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from src.png_grid_extractor import PNGGridExtractor


class TestPNGGridExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.png_dir = os.path.join(self.test_dir, 'png')
        self.output_dir = os.path.join(self.test_dir, 'analysis')
        os.makedirs(self.png_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create a test grid image
        self.test_grid = os.path.join(self.png_dir, 'test_grid.png')
        self._create_test_grid_image(self.test_grid)
    
    def tearDown(self):
        """Tear down test fixtures, if any."""
        # Remove temporary directories
        shutil.rmtree(self.test_dir)
    
    def _create_test_grid_image(self, output_path):
        """Create a test grid image for testing."""
        # Create a blank white image
        image = np.ones((500, 500, 3), np.uint8) * 255
        
        # Draw grid lines
        for i in range(0, 500, 50):
            thickness = 3 if i % 150 == 0 else 1
            cv2.line(image, (0, i), (500, i), (0, 0, 0), thickness)
            cv2.line(image, (i, 0), (i, 500), (0, 0, 0), thickness)
        
        # Add a few numbers
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, '1', (25, 25), font, 0.5, (0, 0, 0), 2)
        cv2.putText(image, '2', (75, 75), font, 0.5, (0, 0, 0), 2)
        cv2.putText(image, '3', (125, 125), font, 0.5, (0, 0, 0), 2)
        
        # Save the image
        cv2.imwrite(output_path, image)
    
    def test_init(self):
        """Test constructor."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir
        )
        self.assertEqual(extractor.input_dir, self.png_dir)
        self.assertEqual(extractor.output_dir, self.output_dir)
    
    def test_scan_for_png_files(self):
        """Test scan_for_png_files method."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir
        )
        
        # Scan for PNG files
        png_files = extractor.scan_for_png_files()
        
        # Check if the test grid was found
        self.assertGreater(len(png_files), 0)
        self.assertIn(self.test_grid, png_files)
    
    def test_detect_grid(self):
        """Test detect_grid method."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir
        )
        
        # Load the test grid image
        image = cv2.imread(self.test_grid)
        
        # Detect the grid
        grid_cells = extractor.detect_grid(image)
        
        # Check if the grid was detected
        self.assertIsNotNone(grid_cells)
        self.assertEqual(len(grid_cells), 9)  # 9 rows
        self.assertEqual(len(grid_cells[0]), 9)  # 9 columns
    
    def test_extract_grid_numbers(self):
        """Test extract_grid_numbers method."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir
        )
        
        # Load the test grid image
        image = cv2.imread(self.test_grid)
        
        # Detect the grid
        grid_cells = extractor.detect_grid(image)
        
        # Extract grid numbers
        grid_numbers, confidence_scores = extractor.extract_grid_numbers(image, grid_cells)
        
        # Check if numbers were extracted
        self.assertIsNotNone(grid_numbers)
        self.assertEqual(len(grid_numbers), 9)  # 9 rows
        self.assertEqual(len(grid_numbers[0]), 9)  # 9 columns
    
    def test_save_grid_to_file(self):
        """Test save_grid_to_file method."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir
        )
        
        # Create a simple grid
        grid = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [None, None, None, None, None, None, None, None, None],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [None, None, None, None, None, None, None, None, None],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [None, None, None, None, None, None, None, None, None],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [None, None, None, None, None, None, None, None, None],
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
        ]
        
        # Create confidence scores
        confidence = [
            [95, 95, 95, 95, 95, 95, 95, 95, 95],
            [None, None, None, None, None, None, None, None, None],
            [95, 95, 95, 95, 95, 95, 95, 95, 95],
            [None, None, None, None, None, None, None, None, None],
            [95, 95, 95, 95, 95, 95, 95, 95, 95],
            [None, None, None, None, None, None, None, None, None],
            [95, 95, 95, 95, 95, 95, 95, 95, 95],
            [None, None, None, None, None, None, None, None, None],
            [95, 95, 95, 95, 95, 95, 95, 95, 95]
        ]
        
        # Create an output file
        output_file = os.path.join(self.output_dir, 'grid.txt')
        
        # Save the grid to file
        extractor.save_grid_to_file(grid, confidence, 1, output_file)
        
        # Check if the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read the file and check its contents
        with open(output_file, 'r') as f:
            contents = f.read()
        
        # Check if the grid header is present
        self.assertIn('Grid 1:', contents)
        
        # Check if the grid is present
        self.assertIn('1', contents)
        self.assertIn('-', contents)
    
    def test_clean_option(self):
        """Test clean option."""
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir,
            clean=True
        )
        
        # Create a dummy file to be cleaned
        dummy_file = os.path.join(self.output_dir, 'dummy.txt')
        with open(dummy_file, 'w') as f:
            f.write('test')
        
        # Process the test grid, which should clean the output directory first
        extractor.process_png_files()
        
        # Check if the dummy file was removed
        self.assertFalse(os.path.exists(dummy_file))
    
    def test_limit_grids(self):
        """Test limit_grids option."""
        # Create multiple test grid images
        for i in range(3):
            test_grid = os.path.join(self.png_dir, f'test_grid{i}.png')
            self._create_test_grid_image(test_grid)
        
        extractor = PNGGridExtractor(
            input_dir=self.png_dir, 
            output_dir=self.output_dir,
            limit_grids=2
        )
        
        # Process the grid images
        processed_files = extractor.process_png_files()
        
        # Check if no more than 2 grids were processed
        self.assertLessEqual(len(processed_files), 2)


if __name__ == '__main__':
    unittest.main() 