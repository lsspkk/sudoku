import cv2
import numpy as np
import logging
from pathlib import Path
import pytesseract
from PIL import Image

class NumberReader:
    def __init__(self):
        # Initialize settings
        self.settings = {
            "cell_padding": 0.15,  # 15% padding
            "threshold_value": 150,
            "preprocessing": {
                "blur_kernel": (3, 3),  # Reduced from (5,5)
                "dilate_kernel": (2, 2),  # Reduced from (3,3)
                "erode_kernel": (2, 2),  # Reduced from (3,3)
                "adaptive_block_size": 11,  # Added for adaptive threshold
                "adaptive_c": 2  # Added for adaptive threshold
            },
            "ocr": {
                "config": "--psm 10 --oem 3 -c tessedit_char_whitelist=123456789",
                "confidence_thresholds": {
                    "high": 70.0,
                    "medium": 40.0,
                    "low": 20.0
                }
            }
        }

    def preprocess_cell(self, cell):
        """Apply preprocessing to improve number detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur with smaller kernel
        blurred = cv2.GaussianBlur(gray, self.settings["preprocessing"]["blur_kernel"], 0)
        
        # Apply adaptive threshold with tuned parameters
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.settings["preprocessing"]["adaptive_block_size"],
            self.settings["preprocessing"]["adaptive_c"]
        )
        
        # Dilate with smaller kernel to connect broken parts
        dilated = cv2.dilate(
            binary,
            np.ones(self.settings["preprocessing"]["dilate_kernel"], np.uint8),
            iterations=1
        )
        
        # Erode with smaller kernel to remove noise
        eroded = cv2.erode(
            dilated,
            np.ones(self.settings["preprocessing"]["erode_kernel"], np.uint8),
            iterations=1
        )
        
        return eroded

    def get_confidence_level(self, confidence):
        """Get confidence level category based on confidence score"""
        if confidence >= self.settings["ocr"]["confidence_thresholds"]["high"]:
            return "high"
        elif confidence >= self.settings["ocr"]["confidence_thresholds"]["medium"]:
            return "medium"
        elif confidence >= self.settings["ocr"]["confidence_thresholds"]["low"]:
            return "low"
        return "failed"

    def recognize_number(self, cell_image):
        """Recognize number in cell with special handling for 1 and 4"""
        # Convert to PIL Image for Tesseract
        pil_image = Image.fromarray(cell_image)
        
        # Get OCR result with confidence
        data = pytesseract.image_to_data(
            pil_image,
            config=self.settings["ocr"]["config"],
            output_type=pytesseract.Output.DICT
        )
        
        # Find the best match
        best_conf = 0
        best_num = None
        all_matches = []
        
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                conf = float(data['conf'][i])
                num = data['text'][i].strip()
                all_matches.append((num, conf))
                if conf > best_conf:
                    best_conf = conf
                    best_num = num
        
        # If no matches or confidence too low, return None
        if best_num is None or best_conf < self.settings["ocr"]["confidence_thresholds"]["low"]:
            return None, 0, "failed", all_matches
        
        # Special handling for 1 and 4
        if best_num in ['1', '4']:
            # Calculate vertical and horizontal line features
            height, width = cell_image.shape
            mid_x = width // 2
            mid_y = height // 2
            
            # Check for horizontal line (characteristic of 4)
            top_half = cell_image[:mid_y, :]
            bottom_half = cell_image[mid_y:, :]
            
            # Count white pixels in each half
            top_white = np.sum(top_half == 255)
            bottom_white = np.sum(bottom_half == 255)
            
            # If there's significant white in both halves, it's likely a 4
            if top_white > width * height * 0.1 and bottom_white > width * height * 0.1:
                return '4', best_conf, self.get_confidence_level(best_conf), all_matches
            else:
                return '1', best_conf, self.get_confidence_level(best_conf), all_matches
        
        return best_num, best_conf, self.get_confidence_level(best_conf), all_matches

    def read_number(self, cell_image):
        """Main method to read a number from a cell image"""
        # Preprocess the cell
        processed = self.preprocess_cell(cell_image)
        
        # Find contours
        contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Recognize number if contours exist
        if len(contours) > 0:
            number, confidence, confidence_level, all_matches = self.recognize_number(processed)
            return {
                "has_content": True,
                "contour_count": len(contours),
                "contour_areas": [cv2.contourArea(c) for c in contours],
                "recognized_number": number,
                "confidence": confidence,
                "confidence_level": confidence_level,
                "all_matches": all_matches
            }
        
        return {
            "has_content": False,
            "contour_count": 0,
            "contour_areas": [],
            "recognized_number": None,
            "confidence": 0,
            "confidence_level": "failed",
            "all_matches": []
        }

def main():
    # Example usage
    reader = NumberReader()
    
    # Test with a sample image
    image_path = Path("pdf/easy_sudoku_booklet_1_fi_4_sudoku1.png")
    if not image_path.exists():
        logging.error(f"Test image not found: {image_path}")
        return
    
    # Read the image
    image = cv2.imread(str(image_path))
    if image is None:
        logging.error(f"Could not read image: {image_path}")
        return
    
    # Calculate cell size
    height, width = image.shape[:2]
    cell_height = height // 9
    cell_width = width // 9
    
    # Test reading a cell (e.g., first cell)
    cell = image[0:cell_height, 0:cell_width]
    result = reader.read_number(cell)
    
    # Log the result
    logging.info(f"Test cell reading result: {result}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main() 