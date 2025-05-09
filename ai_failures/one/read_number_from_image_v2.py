import cv2
import numpy as np
from pathlib import Path
import logging
import pytesseract
from PIL import Image

class NumberReaderV2:
    def __init__(self):
        # Load template images
        self.templates = {}
        self.load_templates()
        
        # Initialize settings
        self.settings = {
            "cell_padding": 0.15,  # 15% padding
            "template_match_threshold": 0.7,  # Minimum similarity threshold
            "preprocessing": {
                "blur_kernel": (3, 3),
                "threshold_value": 150,
                "dilate_kernel": (2, 2),
                "erode_kernel": (2, 2)
            }
        }
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('number_reader_v2.log'),
                logging.StreamHandler()
            ]
        )

    def load_templates(self):
        """Load template images from data directory."""
        data_dir = Path("data")
        for i in range(1, 10):
            template_path = data_dir / f"{i}.png"
            if template_path.exists():
                template = cv2.imread(str(template_path))
                if template is not None:
                    # Convert to grayscale
                    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                    # Normalize
                    template = cv2.normalize(template, None, 0, 255, cv2.NORM_MINMAX)
                    self.templates[str(i)] = template
                    logging.info(f"Loaded template for number {i}")
                else:
                    logging.error(f"Failed to load template for number {i}")
            else:
                logging.error(f"Template file not found: {template_path}")

    def preprocess_cell(self, cell):
        """Apply preprocessing to improve number detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, self.settings["preprocessing"]["blur_kernel"], 0)
        
        # Apply threshold
        _, binary = cv2.threshold(blurred, self.settings["preprocessing"]["threshold_value"], 255, cv2.THRESH_BINARY_INV)
        
        # Dilate to connect broken parts
        dilated = cv2.dilate(
            binary,
            np.ones(self.settings["preprocessing"]["dilate_kernel"], np.uint8),
            iterations=1
        )
        
        # Erode to remove noise
        eroded = cv2.erode(
            dilated,
            np.ones(self.settings["preprocessing"]["erode_kernel"], np.uint8),
            iterations=1
        )
        
        return eroded

    def match_template(self, cell_image):
        """Match the cell image against all templates."""
        best_match = None
        best_score = -1
        best_number = None
        
        # Preprocess the cell
        processed_cell = self.preprocess_cell(cell_image)
        
        # Resize to match template size
        processed_cell = cv2.resize(processed_cell, (64, 64))
        
        # Try template matching for each number
        for number, template in self.templates.items():
            # Calculate similarity using template matching
            result = cv2.matchTemplate(processed_cell, template, cv2.TM_CCOEFF_NORMED)
            score = np.max(result)
            
            if score > best_score:
                best_score = score
                best_number = number
        
        # If the best match is above threshold, return it
        if best_score >= self.settings["template_match_threshold"]:
            return best_number, best_score
        
        # If no good match, try OCR as fallback
        return self.try_ocr(cell_image)

    def try_ocr(self, cell_image):
        """Try OCR as a fallback method."""
        # Convert to PIL Image for Tesseract
        pil_image = Image.fromarray(cell_image)
        
        # Get OCR result
        data = pytesseract.image_to_data(
            pil_image,
            config='--psm 10 --oem 3 -c tessedit_char_whitelist=123456789',
            output_type=pytesseract.Output.DICT
        )
        
        # Find the best match
        best_conf = 0
        best_num = None
        
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                conf = float(data['conf'][i])
                num = data['text'][i].strip()
                if conf > best_conf:
                    best_conf = conf
                    best_num = num
        
        if best_num and best_conf > 60:  # High confidence threshold for OCR
            return best_num, best_conf / 100.0  # Normalize to 0-1 range
        
        return None, 0

    def read_number(self, cell_image):
        """Main method to read a number from a cell image."""
        # Match against templates
        number, confidence = self.match_template(cell_image)
        
        if number:
            # Determine confidence level
            if confidence >= 0.8:
                confidence_level = "high"
            elif confidence >= 0.6:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "has_content": True,
                "recognized_number": number,
                "confidence": confidence * 100,  # Convert to percentage
                "confidence_level": confidence_level,
                "method": "template" if confidence >= self.settings["template_match_threshold"] else "ocr"
            }
        
        return {
            "has_content": False,
            "recognized_number": None,
            "confidence": 0,
            "confidence_level": "failed",
            "method": "none"
        }

def main():
    # Example usage
    reader = NumberReaderV2()
    
    # Test with a sample image
    image_path = Path("tests/png/easy_sudoku_booklet_1_fi_4_sudoku1.png")
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
    main() 