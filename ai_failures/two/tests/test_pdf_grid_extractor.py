#!/usr/bin/env python
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from src.pdf_grid_extractor import PDFGridExtractor


class TestPDFGridExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, 'png')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Get path to test PDF
        self.test_pdf = os.path.join('pdf', 'easy_sudoku_booklet_1_fi_4.pdf')
        
        # Check if the test PDF exists
        if not os.path.exists(self.test_pdf):
            self.skipTest(f"Test PDF {self.test_pdf} not found")
    
    def tearDown(self):
        """Tear down test fixtures, if any."""
        # Remove temporary directories
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test constructor."""
        extractor = PDFGridExtractor(
            input_file=self.test_pdf, 
            output_dir=self.output_dir
        )
        self.assertEqual(extractor.input_file, self.test_pdf)
        self.assertEqual(extractor.output_dir, self.output_dir)
    
    def test_extract_pages(self):
        """Test extract_pages method."""
        extractor = PDFGridExtractor(
            input_file=self.test_pdf, 
            output_dir=self.output_dir
        )
        
        # Extract the first page only
        extractor.limit_pages = 1
        png_files = extractor.extract_pages()
        
        # Check if a PNG file was created
        self.assertGreater(len(png_files), 0)
        
        # Check if the file exists
        self.assertTrue(os.path.exists(png_files[0]))
    
    def test_clean_option(self):
        """Test clean option."""
        extractor = PDFGridExtractor(
            input_file=self.test_pdf, 
            output_dir=self.output_dir,
            clean=True
        )
        
        # Create a dummy file to be cleaned
        dummy_file = os.path.join(self.output_dir, 'dummy.png')
        with open(dummy_file, 'w') as f:
            f.write('test')
        
        # Extract pages, which should clean the output directory first
        extractor.extract_pages()
        
        # Check if the dummy file was removed
        self.assertFalse(os.path.exists(dummy_file))
    
    def test_limit_pages(self):
        """Test limit_pages option."""
        extractor = PDFGridExtractor(
            input_file=self.test_pdf, 
            output_dir=self.output_dir
        )
        
        # Set limit to 2 pages
        extractor.limit_pages = 2
        png_files = extractor.extract_pages()
        
        # Check if no more than 2 pages were extracted
        self.assertLessEqual(len(png_files), 2)


if __name__ == '__main__':
    unittest.main() 