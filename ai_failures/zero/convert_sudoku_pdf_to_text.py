import os
import json
import datetime
import traceback
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract
import logging
from text_sudoku import format_sudoku_grid

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
png_dir = logs_dir / "png"
logs_dir.mkdir(exist_ok=True)
png_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'pdf_conversion.log'),
        logging.StreamHandler()
    ]
)

# Configure conversion output logging
conversion_logger = logging.getLogger('conversion_output')
conversion_logger.setLevel(logging.INFO)
conversion_handler = logging.FileHandler(logs_dir / 'conversion_output.log')
conversion_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
conversion_logger.addHandler(conversion_handler)

class SudokuPDFConverter:
    def __init__(self):
        self.pdf_folder = Path("pdf")
        self.status_file = logs_dir / "pdf_read_status.json"
        self.load_status()
        self.scale_factor = 4  # Scale images 4x larger

    def load_status(self):
        """Load existing status from JSON file"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                self.status = json.load(f)
        else:
            self.status = {"status": []}

    def save_status(self):
        """Save current status to JSON file"""
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, indent=2)

    def get_processed_files(self):
        """Get list of already processed files"""
        return {entry["file"] for entry in self.status["status"]}

    def find_grids(self, image):
        """Find all potential Sudoku grids in the image"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and aspect ratio
        grids = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = w * h
            
            # Sudoku grids should be roughly square and have a reasonable size
            if 0.8 < aspect_ratio < 1.2 and area > 10000:
                grid = image[y:y+h, x:x+w]
                grids.append((grid, (x, y, w, h)))
        
        return grids

    def recognize_digits(self, grid):
        """Recognize digits in the grid using Tesseract OCR"""
        # Convert to grayscale
        gray = cv2.cvtColor(grid, cv2.COLOR_BGR2GRAY)
        
        # Split into 9x9 cells
        height, width = gray.shape
        cell_height = height // 9
        cell_width = width // 9
        
        sudoku_grid = []
        cell_details = []
        
        for i in range(9):
            row = []
            row_details = []
            for j in range(9):
                # Extract cell
                cell = gray[i*cell_height:(i+1)*cell_height, 
                          j*cell_width:(j+1)*cell_width]
                
                # Use OCR to recognize digit
                digit = pytesseract.image_to_string(
                    cell, 
                    config='--psm 10 --oem 3 -c tessedit_char_whitelist=123456789'
                ).strip()
                
                # Get confidence score
                data = pytesseract.image_to_data(
                    cell,
                    config='--psm 10 --oem 3 -c tessedit_char_whitelist=123456789',
                    output_type=pytesseract.Output.DICT
                )
                
                confidence = data['conf'][0] if data['conf'] else 0
                
                row.append(digit if digit else '-')
                row_details.append({
                    'digit': digit if digit else '-',
                    'confidence': confidence
                })
            
            sudoku_grid.append(row)
            cell_details.append(row_details)
        
        return sudoku_grid, cell_details

    def convert_grid_to_text_format(self, grid):
        """Convert recognized grid to text format"""
        return '\n'.join(' '.join(row) for row in grid)

    def save_grid_image(self, grid, pdf_path, grid_number):
        """Save grid image to file with 4x scaling"""
        # Scale the grid image
        height, width = grid.shape[:2]
        scaled_grid = cv2.resize(grid, (width * self.scale_factor, height * self.scale_factor), 
                               interpolation=cv2.INTER_CUBIC)
        
        # Save the scaled image to logs/png directory
        output_path = png_dir / f"{pdf_path.stem}_sudoku{grid_number}.png"
        cv2.imwrite(str(output_path), scaled_grid)
        
        # Log the scaling information
        conversion_logger.info(f"Original grid size: {width}x{height}")
        conversion_logger.info(f"Scaled grid size: {width * self.scale_factor}x{height * self.scale_factor}")
        
        return output_path

    def process_pdf(self, pdf_path):
        """Process a single PDF file"""
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Convert first page to image with higher resolution
            page = doc[0]
            zoom = 2  # Increase initial zoom for better quality
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = np.array(img)
            
            # Find all grids
            grids = self.find_grids(img_np)
            
            if not grids:
                raise ValueError("Could not find any Sudoku grids in the image")
            
            conversion_logger.info(f"\nProcessing {pdf_path}")
            conversion_logger.info(f"Found {len(grids)} potential Sudoku grids")
            
            # Process each grid
            for i, (grid, (x, y, w, h)) in enumerate(grids, 1):
                # Save grid image (now with 4x scaling)
                grid_path = self.save_grid_image(grid, pdf_path, i)
                conversion_logger.info(f"\nGrid {i} at position ({x}, {y}) with size {w}x{h}")
                
                # Recognize digits
                sudoku_grid, cell_details = self.recognize_digits(grid)
                
                # Log recognition details
                conversion_logger.info("Recognized digits and confidence scores:")
                for row_idx, row in enumerate(cell_details):
                    row_str = " ".join(f"{cell['digit']}({cell['confidence']:.1f})" for cell in row)
                    conversion_logger.info(f"Row {row_idx + 1}: {row_str}")
                
                # Convert to text format
                text_format = self.convert_grid_to_text_format(sudoku_grid)
                
                # Save to text file
                output_path = png_dir / f"{pdf_path.stem}_sudoku{i}.txt"
                with open(output_path, 'w') as f:
                    f.write(text_format)
                
                conversion_logger.info(f"Saved grid {i} to {output_path}")
            
            return True, None
            
        except Exception as e:
            return False, str(e)

    def process_all_pdfs(self):
        """Process all unprocessed PDF files in the pdf folder"""
        processed_files = self.get_processed_files()
        
        for pdf_file in self.pdf_folder.glob("*.pdf"):
            if str(pdf_file) in processed_files:
                continue
                
            logging.info(f"Processing {pdf_file}")
            
            success, error = self.process_pdf(pdf_file)
            
            # Record status
            status_entry = {
                "file": str(pdf_file),
                "timestamp": datetime.datetime.now().isoformat(),
                "success": success,
                "error": error
            }
            
            self.status["status"].append(status_entry)
            self.save_status()
            
            if not success:
                logging.error(f"Error processing {pdf_file}: {error}")

def process_image(image_path, output_dir):
    """Process a single image and save results."""
    # ... existing code until grid creation ...

    # Format and save grid
    formatted_grid = format_sudoku_grid(grid)
    with open(output_dir / 'recognized_grids.txt', 'a') as f:
        f.write(f"\nGrid from {image_path.name}:\n")
        f.write(formatted_grid)
        f.write("\n\n")

    return grid

def main():
    # Move any existing PNG files to logs/png directory
    pdf_dir = Path("pdf")
    for png_file in pdf_dir.glob("*.png"):
        target_path = png_dir / png_file.name
        if target_path.exists():
            target_path.unlink()  # Remove existing file
        png_file.rename(target_path)
        logging.info(f"Moved {png_file} to {target_path}")
    
    # Clear previous output files
    for file in png_dir.glob('*'):
        file.unlink()
    
    # Clear recognized_grids.txt
    with open(png_dir / 'recognized_grids.txt', 'w') as f:
        f.write("Recognized Sudoku Grids:\n")
        f.write("=" * 50 + "\n")

    converter = SudokuPDFConverter()
    converter.process_all_pdfs()

if __name__ == "__main__":
    main() 