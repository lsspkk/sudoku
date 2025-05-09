import os
import json
import datetime
import traceback
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import logging
from text_sudoku import format_sudoku_grid
from enhance_images import enhance_image
from extract_number_from_image import extract_number_from_cell_data

# --- Configuration ---
PDF_FOLDER = Path("pdf")
LOGS_DIR = Path("logs")
STATUS_FILE = LOGS_DIR / "pdf_read_status_v2.json"
LOG_FILE = LOGS_DIR / 'extract_analysis.log'
GRIDS_TXT_PATH = LOGS_DIR / 'grids.txt'
GRIDS_ANALYSIS_PATH = LOGS_DIR / 'grids_analysis.txt'
ENHANCED_PNG_DIR = LOGS_DIR / "enhanced_pngs" # Separate folder for enhanced images
INITIAL_PDF_ZOOM = 2 # Initial zoom factor for PDF page rendering
GRID_SCALE_FACTOR = 4 # Scale factor for saving enhanced grid PNGs
GRID_AREA_THRESHOLD = 10000 # Minimum pixel area to consider a contour a grid
GRID_ASPECT_RATIO_MIN = 0.8
GRID_ASPECT_RATIO_MAX = 1.2

# --- Setup Logging ---
LOGS_DIR.mkdir(exist_ok=True)
ENHANCED_PNG_DIR.mkdir(exist_ok=True)

# Clear previous log file
if LOG_FILE.exists():
    LOG_FILE.unlink()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Also print logs to console
    ]
)

class SudokuPDFConverterV2:
    def __init__(self):
        self.pdf_folder = PDF_FOLDER
        self.status_file = STATUS_FILE
        self.enhanced_png_dir = ENHANCED_PNG_DIR
        self.load_status()
        self.total_stats = {
            "sudokus_processed": 0,
            "numbers_recognized": 0,
            "numbers_unrecognized": 0
        }

    def load_status(self):
        """Load existing status from JSON file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    self.status = json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"Could not decode status file {self.status_file}, starting fresh.")
                self.status = {"status": []}
        else:
            self.status = {"status": []}

    def save_status(self):
        """Save current status to JSON file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except IOError as e:
            logging.error(f"Could not save status file {self.status_file}: {e}")

    def get_processed_files(self):
        """Get list of already processed files"""
        return {entry["file"] for entry in self.status.get("status", [])}

    def find_grids(self, image):
        """Find all potential Sudoku grids in the image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        grids = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = w * h
            
            if GRID_ASPECT_RATIO_MIN < aspect_ratio < GRID_ASPECT_RATIO_MAX and area > GRID_AREA_THRESHOLD:
                # Extract the grid using original image coordinates
                grid_image_data = image[y:y+h, x:x+w]
                grids.append((grid_image_data, (x, y, w, h)))
        
        logging.info(f"Found {len(grids)} potential grid contours.")
        return grids

    def save_enhanced_grid_image(self, enhanced_grid_data, pdf_stem, grid_number):
        """Save enhanced grid image to file with scaling"""
        try:
            height, width = enhanced_grid_data.shape[:2]
            scaled_grid = cv2.resize(enhanced_grid_data,
                                     (width * GRID_SCALE_FACTOR, height * GRID_SCALE_FACTOR),
                                     interpolation=cv2.INTER_CUBIC)
            
            output_filename = f"{pdf_stem}_sudoku{grid_number}.png"
            output_path = self.enhanced_png_dir / output_filename
            cv2.imwrite(str(output_path), scaled_grid)
            logging.info(f"Saved enhanced grid {grid_number} to {output_path} (scaled {GRID_SCALE_FACTOR}x)")
            return str(output_path)
        except Exception as e:
            logging.error(f"Failed to save enhanced grid image {grid_number} for {pdf_stem}: {e}")
            return None

    def recognize_digits_and_analyze(self, enhanced_grid_data):
        """Recognize digits, determine confidence, and prepare analysis grid"""
        height, width = enhanced_grid_data.shape[:2]
        if height == 0 or width == 0:
             logging.warning("Received empty grid data for recognition.")
             return [], [], 0, 0 # Return empty grids and zero counts
             
        cell_height = height // 9
        cell_width = width // 9
        
        grid_numbers_only = []
        grid_analysis = []
        recognized_count = 0
        unrecognized_count = 0
        
        for i in range(9):
            row_numbers = []
            row_analysis = []
            for j in range(9):
                y1, y2 = i * cell_height, (i + 1) * cell_height
                x1, x2 = j * cell_width, (j + 1) * cell_width
                cell_image = enhanced_grid_data[y1:y2, x1:x2]
                
                if cell_image.size == 0:
                     logging.warning(f"Empty cell slice at grid ({i},{j})")
                     number, confidence = '', -1.0
                else:
                    try:
                         number, confidence = extract_number_from_cell_data(cell_image)
                    except Exception as e:
                         logging.error(f"Error extracting number from cell ({i},{j}): {e}")
                         number, confidence = '', -1.0
                
                if number:
                    recognized_count += 1
                    row_numbers.append(number)
                    # Determine confidence letter
                    if confidence >= 90:
                        conf_letter = 'H'
                    elif confidence >= 50:
                        conf_letter = 'M'
                    elif confidence >= 0:
                        conf_letter = 'L' # Confidence was reported but low
                    else:
                         conf_letter = '' # Confidence was -1 (not reported)
                    row_analysis.append(f"{number}{conf_letter}")
                else:
                    unrecognized_count += 1
                    row_numbers.append('-')
                    row_analysis.append('--')
            
            grid_numbers_only.append(row_numbers)
            grid_analysis.append(row_analysis)
        
        return grid_numbers_only, grid_analysis, recognized_count, unrecognized_count

    def process_pdf(self, pdf_path):
        """Process a single PDF file"""
        grid_stats = {"recognized": 0, "unrecognized": 0}
        try:
            doc = fitz.open(pdf_path)
            if not doc.page_count > 0:
                 raise ValueError("PDF has no pages.")
                 
            page = doc[0]
            mat = fitz.Matrix(INITIAL_PDF_ZOOM, INITIAL_PDF_ZOOM)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            grids_found = self.find_grids(img_np)
            if not grids_found:
                raise ValueError("Could not find any potential Sudoku grids in the PDF's first page")
            
            pdf_stem = pdf_path.stem
            logging.info(f"Processing {len(grids_found)} grids from {pdf_path.name}")

            # Append to existing files
            with open(GRIDS_TXT_PATH, 'a') as grids_txt_file, \
                 open(GRIDS_ANALYSIS_PATH, 'a') as grids_analysis_file:

                for i, (grid_data, (x, y, w, h)) in enumerate(grids_found, 1):
                    logging.info(f"--- Processing Grid {i} [Pos:({x},{y}), Size:({w}x{h})] ---")
                    enhanced_grid = enhance_image(grid_data)
                    
                    # Save the enhanced PNG (optional, but useful for debugging)
                    self.save_enhanced_grid_image(enhanced_grid, pdf_stem, i)
                    
                    # Recognize digits and get analysis
                    grid_numbers, grid_analysis_details, rec_count, unrec_count = \
                        self.recognize_digits_and_analyze(enhanced_grid)
                    
                    grid_stats["recognized"] += rec_count
                    grid_stats["unrecognized"] += unrec_count
                    logging.info(f"Grid {i} Stats: Recognized={rec_count}, Unrecognized={unrec_count}")

                    # Format grids for output
                    formatted_numbers_grid = format_sudoku_grid(grid_numbers)
                    formatted_analysis_grid = format_sudoku_grid(grid_analysis_details)
                    
                    # Write to files
                    grids_txt_file.write(f"\nGrid {i} from {pdf_path.name}:\n")
                    grids_txt_file.write(formatted_numbers_grid + "\n")
                    
                    grids_analysis_file.write(f"\nGrid {i} from {pdf_path.name} (Confidence: H>90, M>50, L>=0):\n")
                    grids_analysis_file.write(formatted_analysis_grid + "\n")
            
            doc.close()
            return True, None, grid_stats
            
        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")
            traceback.print_exc() # Print detailed traceback to console/log
            # Ensure doc is closed if opened
            if 'doc' in locals() and doc.is_open:
                 doc.close()
            return False, str(e), grid_stats # Return stats even on failure

    def process_all_pdfs(self):
        """Process all unprocessed PDF files in the pdf folder"""
        logging.info("Starting PDF processing run...")
        processed_files = self.get_processed_files()
        pdfs_to_process = [p for p in self.pdf_folder.glob("*.pdf") if str(p) not in processed_files]
        
        if not pdfs_to_process:
             logging.info("No new PDF files found to process.")
             return
             
        logging.info(f"Found {len(pdfs_to_process)} new PDF files.")

        # Clear/Initialize output text files for this run
        with open(GRIDS_TXT_PATH, 'w') as f: f.write("Sudoku Grids:\n" + "=" * 50 + "\n")
        with open(GRIDS_ANALYSIS_PATH, 'w') as f: f.write("Sudoku Grids Analysis:\n" + "=" * 50 + "\n")
        
        for pdf_file in pdfs_to_process:
            logging.info(f"=== Processing {pdf_file.name} ===")
            success, error, stats = self.process_pdf(pdf_file)
            
            # Update total stats
            if success:
                self.total_stats["sudokus_processed"] += 1 # Count PDF as processed if successful
            self.total_stats["numbers_recognized"] += stats["recognized"]
            self.total_stats["numbers_unrecognized"] += stats["unrecognized"]

            # Record status
            status_entry = {
                "file": str(pdf_file),
                "timestamp": datetime.datetime.now().isoformat(),
                "success": success,
                "error": error,
                "recognized_in_pdf": stats["recognized"],
                "unrecognized_in_pdf": stats["unrecognized"]
            }
            self.status.setdefault("status", []).append(status_entry)
            self.save_status()
            
            if success:
                 logging.info(f"Successfully processed {pdf_file.name}")
            else:
                 logging.error(f"Failed to process {pdf_file.name}. See logs for details.")

        # Log final statistics
        logging.info("=== PDF Processing Run Summary ===")
        logging.info(f"Total Sudoku PDFs Processed Successfully in this run: {self.total_stats['sudokus_processed']}")
        logging.info(f"Total Numbers Recognized in this run: {self.total_stats['numbers_recognized']}")
        logging.info(f"Total Numbers Unrecognized in this run: {self.total_stats['numbers_unrecognized']}")
        logging.info("Processing complete.")


if __name__ == "__main__":
    # Optional: Clear enhanced PNGs from previous runs
    # for png_file in ENHANCED_PNG_DIR.glob("*.png"):
    #     try:
    #         png_file.unlink()
    #     except OSError as e:
    #         logging.warning(f"Could not delete old PNG {png_file}: {e}")
            
    converter = SudokuPDFConverterV2()
    converter.process_all_pdfs() 