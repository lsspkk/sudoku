#!/usr/bin/env python
import os
import sys
import argparse
import logging
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image

class PDFGridExtractor:
    def __init__(self, input_file=None, output_dir="logs/png", clean=False, limit_pages=None, scale_factor=4):
        """
        Initialize the PDF grid extractor.
        Args:
            input_file: Path to the input PDF file
            output_dir: Directory to save the extracted PNG files
            clean: Whether to clean the output directory before extraction
            limit_pages: Maximum number of pages to extract (None for all pages)
            scale_factor: How much to scale up the cropped grid images
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.clean = clean
        self.limit_pages = limit_pages
        self.scale_factor = scale_factor
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join('logs', 'pdf_grid_extractor.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('pdf_grid_extractor')
        os.makedirs(output_dir, exist_ok=True)

    def find_grids(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        grids = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = w * h
            if 0.8 < aspect_ratio < 1.2 and area > 10000:
                grid = image[y:y+h, x:x+w]
                grids.append((grid, (x, y, w, h)))
        return grids

    def extract_pages(self):
        self.logger.info(f"Extracting grids from {self.input_file}")
        if self.clean and os.path.exists(self.output_dir):
            self.logger.info(f"Cleaning output directory: {self.output_dir}")
            for file in os.listdir(self.output_dir):
                path = os.path.join(self.output_dir, file)
                if os.path.isfile(path):
                    os.remove(path)
        pdf_basename = os.path.splitext(os.path.basename(self.input_file))[0]
        try:
            doc = fitz.open(self.input_file)
            num_pages = len(doc)
            first_page = 0
            last_page = num_pages if self.limit_pages is None else min(num_pages, self.limit_pages)
            saved_files = []
            for page_num in range(first_page, last_page):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_np = np.array(img)
                grids = self.find_grids(img_np)
                if not grids:
                    self.logger.warning(f"No grids found on page {page_num+1}")
                    continue
                for i, (grid, (x, y, w, h)) in enumerate(grids, 1):
                    height, width = grid.shape[:2]
                    scaled_grid = cv2.resize(grid, (width * self.scale_factor, height * self.scale_factor), interpolation=cv2.INTER_CUBIC)
                    output_file = os.path.join(self.output_dir, f"{pdf_basename}_p{page_num+1}_g{i}.png")
                    cv2.imwrite(output_file, scaled_grid)
                    self.logger.info(f"Saved grid {i} from page {page_num+1} to {output_file}")
                    saved_files.append(output_file)
            return saved_files
        except Exception as e:
            self.logger.error(f"Error extracting grids from {self.input_file}: {e}")
            raise

    def process_pdf(self):
        if not self.input_file:
            self.logger.error("No input file specified")
            return []
        if not os.path.exists(self.input_file):
            self.logger.error(f"Input file not found: {self.input_file}")
            return []
        try:
            return self.extract_pages()
        except Exception as e:
            self.logger.error(f"Error processing {self.input_file}: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='Extract Sudoku grids from PDF files')
    parser.add_argument('--input', help='Path to the input PDF file (if omitted, process all in pdf/)')
    parser.add_argument('--output_dir', default='logs/png', help='Directory to save the extracted PNG files')
    parser.add_argument('--clean', action='store_true', help='Clean the output directory before extraction')
    parser.add_argument('--limit_pages', type=int, help='Maximum number of pages to extract')
    parser.add_argument('--scale_factor', type=int, default=4, help='Scale factor for cropped grid images')
    args = parser.parse_args()

    if args.input:
        pdf_files = [args.input]
    else:
        pdf_dir = Path('pdf')
        pdf_files = sorted(str(f) for f in pdf_dir.glob('*.pdf'))
        if not pdf_files:
            print('No PDF files found in pdf/ directory.')
            return 1
        print(f'Found {len(pdf_files)} PDF files in pdf/:')
        for f in pdf_files:
            print(f'  {f}')

    total_grids = 0
    for idx, pdf_file in enumerate(pdf_files):
        print(f"\nProcessing {pdf_file} ({idx+1}/{len(pdf_files)})...")
        extractor = PDFGridExtractor(
            input_file=pdf_file,
            output_dir=args.output_dir,
            clean=args.clean if idx == 0 else False,  # Only clean for the first file
            limit_pages=args.limit_pages,
            scale_factor=args.scale_factor
        )
        png_files = extractor.process_pdf()
        if png_files:
            print(f"Extracted {len(png_files)} grid images from {pdf_file}")
            total_grids += len(png_files)
        else:
            print(f"No grids extracted from {pdf_file}")
    print(f"\nDone. Total grids extracted: {total_grids}")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 