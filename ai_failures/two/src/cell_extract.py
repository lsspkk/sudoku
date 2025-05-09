#!/usr/bin/env python
import os
import sys
import logging
import numpy as np
import cv2
import pytesseract
import yaml
import traceback
from pathlib import Path
from datetime import datetime

# Setup basic logging to stdout for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("extract_cell_debug")

try:
    # Test pytesseract installation
    logger.info("Testing pytesseract installation...")
    pytesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {pytesseract_version}")
    
    # Test OpenCV installation
    logger.info("Testing OpenCV installation...")
    logger.info(f"OpenCV version: {cv2.__version__}")
    
    # Test YAML installation
    logger.info("Testing YAML installation...")
    yaml_data = yaml.safe_load('a: 1')
    logger.info(f"YAML test: {yaml_data}")
    
    # Test directory access
    logger.info("Testing directory access...")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/debug", exist_ok=True)
    logger.info("Successfully created logs directories")
    
except Exception as e:
    logger.error(f"Initialization error: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

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

class CellExtractor:
    def __init__(self, config_path: str):
        """
        Initialize the cell extractor with configuration.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        try:
            self.logger = SimpleLogger(os.path.join('logs', 'extract_cell.log'))
            self.logger.info(f"Initializing CellExtractor with config: {config_path}")
            
            # Check if config file exists
            if not os.path.exists(config_path):
                self.logger.error(f"Config file not found: {config_path}")
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            self.config = self._load_config(config_path)
            self._validate_config()
            
            # Adjusted configuration values for better OCR and preprocessing
            self.config['min_contour_area'] = 100
            self.config['max_contour_area'] = 5000
            self.config['preprocessing']['threshold_value'] = 150
            self.config['preprocessing']['blur_kernel_size'] = 5
            self.config['tesseract_config'] = '--psm 6 --oem 3 -c tessedit_char_whitelist=123456789'
            
            # Create debug directory if needed
            if self.config['save_debug_images']:
                debug_dir = self.config['debug_output_dir']
                self.logger.info(f"Creating debug directory: {debug_dir}")
                os.makedirs(debug_dir, exist_ok=True)
                
            self.logger.info("CellExtractor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error in CellExtractor.__init__: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _load_config(self, config_path: str) -> dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Dictionary containing configuration
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            raise ValueError(f"Failed to load configuration file: {e}")
    
    def _validate_config(self):
        """Validate the configuration."""
        required_keys = [
            'cell_padding', 
            'cell_border_width', 
            'min_contour_area', 
            'max_contour_area',
            'tesseract_config',
            'confidence_thresholds',
            'preprocessing',
            'save_debug_images',
            'debug_output_dir'
        ]
        
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        if not isinstance(self.config['confidence_thresholds'], dict):
            raise ValueError("confidence_thresholds must be a dictionary")
        
        required_thresholds = ['high', 'medium', 'low']
        for threshold in required_thresholds:
            if threshold not in self.config['confidence_thresholds']:
                raise ValueError(f"Missing required threshold: {threshold}")
        
        if not isinstance(self.config['preprocessing'], dict):
            raise ValueError("preprocessing must be a dictionary")
        
        required_preprocessing = ['blur_kernel_size', 'threshold_value', 'threshold_type', 'morph_kernel_size']
        for key in required_preprocessing:
            if key not in self.config['preprocessing']:
                raise ValueError(f"Missing required preprocessing key: {key}")
    
    def extract_cell(self, image_data: np.ndarray, x: int, y: int, width: int, height: int, grid_number: int = 1, row: int = 0, col: int = 0) -> dict:
        """
        Extract and analyze a cell from the image.
        
        Args:
            image_data: The source image as numpy array
            x, y: Top-left coordinates of the cell
            width, height: Dimensions of the cell
            grid_number: The grid number (default 1)
            row, col: Grid coordinates (0-8)
            
        Returns:
            Dictionary containing:
            - number: Recognized number or None
            - confidence: Confidence score (0-100) or None
            - confidence_level: 'high', 'medium', 'low', or 'failed'
            - has_content: Boolean indicating if cell contains any content
            - debug_info: Additional debug information if enabled
            - all_matches: List of all recognized numbers and their confidence scores
        """
        # Extract the cell region from the image
        cell_image = self._extract_cell_region(image_data, x, y, width, height)
        
        # Check if the cell contains any content
        has_content, content_mask = self._check_cell_content(cell_image)
        
        # Initialize result dictionary
        result = {
            'number': None,
            'confidence': None,
            'confidence_level': 'failed',
            'has_content': has_content,
            'debug_info': {},
            'all_matches': []
        }
        
        # If the cell has no content, return early
        if not has_content:
            self.logger.debug(f"Cell at (grid={grid_number}, row={row}, col={col}, x={x}, y={y}) has no content")
            return result
        
        # Preprocess the cell image
        preprocessed = self._preprocess_cell_image(cell_image, content_mask)
        
        # Save debug images if enabled
        if self.config['save_debug_images']:
            self._save_debug_images(cell_image, content_mask, preprocessed, x, y, grid_number, row, col)
        
        # Recognize the number (improved logic)
        number, confidence, all_matches = self._perform_ocr(preprocessed)
        
        # Update the result
        result['number'] = number
        result['confidence'] = confidence
        result['all_matches'] = all_matches
        
        # Determine confidence level
        if number is not None and confidence is not None:
            thresholds = self.config['confidence_thresholds']
            if confidence >= thresholds['high']:
                result['confidence_level'] = 'high'
            elif confidence >= thresholds['medium']:
                result['confidence_level'] = 'medium'
            elif confidence >= thresholds['low']:
                result['confidence_level'] = 'low'
            else:
                result['confidence_level'] = 'failed'
        
        self.logger.debug(f"Cell at (grid={grid_number}, row={row}, col={col}, x={x}, y={y}): number={number}, confidence={confidence}, level={result['confidence_level']}")
        return result
    
    def _extract_cell_region(self, image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """
        Extract the cell region from the image.
        
        Args:
            image: The source image
            x, y: Top-left coordinates of the cell
            width, height: Dimensions of the cell
            
        Returns:
            Cell image as numpy array
        """
        # Apply padding if needed
        padding = self.config['cell_padding']
        border = self.config['cell_border_width']
        
        # Calculate new coordinates with padding and border
        x1 = x + border
        y1 = y + border
        x2 = x + width - border
        y2 = y + height - border
        
        # Ensure coordinates are within image boundaries
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)
        
        # Extract the cell region
        cell_image = image[y1:y2, x1:x2]
        
        return cell_image
    
    def _check_cell_content(self, cell_image: np.ndarray) -> tuple:
        """
        Check if the cell contains any content.
        
        Args:
            cell_image: The cell image
            
        Returns:
            Tuple containing:
            - Boolean indicating if the cell has content
            - Content mask if cell has content, None otherwise
        """
        # Convert to grayscale
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()
        
        # Apply Gaussian blur
        blur_size = self.config['preprocessing']['blur_kernel_size']
        blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        
        # Apply binary threshold
        threshold_value = self.config['preprocessing']['threshold_value']
        _, binary = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check if any contour meets the size criteria
        min_area = self.config['min_contour_area']
        max_area = self.config['max_contour_area']
        
        content_mask = np.zeros_like(binary)
        has_content = False
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                cv2.drawContours(content_mask, [contour], -1, 255, -1)
                has_content = True
        
        return has_content, content_mask
    
    def _preprocess_cell_image(self, cell_image: np.ndarray, content_mask: np.ndarray) -> np.ndarray:
        """
        Preprocess the cell image for OCR.
        
        Args:
            cell_image: The cell image
            content_mask: The content mask
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()
        
        # Apply preprocessing
        preproc = self.config['preprocessing']
        
        # Apply Gaussian blur
        blur_size = preproc['blur_kernel_size']
        blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        
        # Apply threshold
        threshold_value = preproc['threshold_value']
        threshold_type_str = preproc['threshold_type']
        threshold_type = getattr(cv2, threshold_type_str)
        _, binary = cv2.threshold(blurred, threshold_value, 255, threshold_type)
        
        # Apply morphological operations
        kernel_size = preproc['morph_kernel_size']
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        morph = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Apply content mask
        masked = cv2.bitwise_and(morph, content_mask)
        
        return masked
    
    def _perform_ocr(self, image: np.ndarray) -> tuple:
        """
        Perform OCR on the preprocessed image.
        Returns:
            - Recognized number or None
            - Confidence score (0-100) or None
            - All matches (for debugging)
        """
        try:
            config = self.config['tesseract_config']
            result = pytesseract.image_to_data(
                image,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            matches = []
            for i, text in enumerate(result['text']):
                text = text.strip()
                if text.isdigit():
                    number = int(text)
                    if 1 <= number <= 9:
                        try:
                            conf = float(result['conf'][i])
                        except Exception:
                            conf = 50.0
                        matches.append((number, conf))
            # Fallback: try image_to_string if no matches
            if not matches:
                text = pytesseract.image_to_string(image, config=config)
                text = ''.join(filter(str.isdigit, text))
                for char in text:
                    number = int(char)
                    if 1 <= number <= 9:
                        matches.append((number, 50.0))  # Assign a default confidence
            if matches:
                # Return the match with the highest confidence
                matches.sort(key=lambda x: x[1], reverse=True)
                return matches[0][0], matches[0][1], matches
            return None, None, matches
        except Exception as e:
            self.logger.error(f"OCR error: {e}")
            return None, None, []
    
    def _save_debug_images(self, original: np.ndarray, mask: np.ndarray, preprocessed: np.ndarray, x: int, y: int, grid_number: int = 1, row: int = 0, col: int = 0):
        """
        Save debug images.
        Args:
            original: The original cell image
            mask: The content mask
            preprocessed: The preprocessed image
            x, y: Pixel coordinates (for internal use)
            grid_number: The grid number (default 1)
            row, col: Grid coordinates (0-8)
        """
        output_dir = self.config['debug_output_dir']
        base_filename = f"grid{grid_number}_{row}_{col}"
        # Save original image
        cv2.imwrite(os.path.join(output_dir, f"{base_filename}_original.png"), original)
        # Save content mask
        cv2.imwrite(os.path.join(output_dir, f"{base_filename}_mask.png"), mask)
        # Save preprocessed image
        cv2.imwrite(os.path.join(output_dir, f"{base_filename}_preprocessed.png"), preprocessed)

    def analyze_cell(self, image_data: np.ndarray, x: int, y: int, width: int, height: int, digit_whitelist: str = '123456789') -> dict:
        """
        Analyze a cell by trying multiple config values to maximize OCR accuracy.
        Saves all attempted cell images to logs/analyze/ and logs results to logs/extract_cell.log.
        Returns the best result found.
        """
        import itertools
        analyze_dir = os.path.join('logs', 'analyze')
        os.makedirs(analyze_dir, exist_ok=True)
        log_path = os.path.join('logs', 'extract_cell.log')
        # Try multiple values for threshold, blur, tesseract config
        threshold_values = [self.config['preprocessing']['threshold_value'], 100, 127, 150, 180]
        blur_kernels = [self.config['preprocessing']['blur_kernel_size'], 1, 3, 5]
        tesseract_configs = [
            self.config['tesseract_config'],
            '--psm 10 --oem 3',
            '--psm 8 --oem 3',
            f"--psm 10 --oem 3 -c tessedit_char_whitelist={digit_whitelist}",
            f"--psm 8 --oem 3 -c tessedit_char_whitelist={digit_whitelist}"
        ]
        best_result = None
        best_conf = -1
        attempt = 0
        for thresh, blur, tess_cfg in itertools.product(threshold_values, blur_kernels, tesseract_configs):
            # Preprocess cell with these params
            cell_image = self._extract_cell_region(image_data, x, y, width, height)
            # Convert to grayscale
            if len(cell_image.shape) == 3:
                gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = cell_image.copy()
            # Blur
            blurred = cv2.GaussianBlur(gray, (blur, blur), 0) if blur > 1 else gray
            # Threshold
            _, binary = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY_INV)
            # Morph
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            # Save debug image
            img_filename = f"cell_{x}_{y}_t{thresh}_b{blur}_psm{tess_cfg.replace(' ', '').replace('--', '').replace('=', '')}_{attempt}.png"
            cv2.imwrite(os.path.join(analyze_dir, img_filename), morph)
            # OCR
            try:
                result = pytesseract.image_to_data(
                    morph,
                    config=tess_cfg,
                    output_type=pytesseract.Output.DICT
                )
                matches = []
                for i, text in enumerate(result['text']):
                    text = text.strip()
                    if text.isdigit():
                        number = int(text)
                        if 1 <= number <= 9:
                            try:
                                conf = float(result['conf'][i])
                            except Exception:
                                conf = 50.0
                            matches.append((number, conf))
                # Fallback: try image_to_string if no matches
                if not matches:
                    text = pytesseract.image_to_string(morph, config=tess_cfg)
                    text = ''.join(filter(str.isdigit, text))
                    for char in text:
                        number = int(char)
                        if 1 <= number <= 9:
                            matches.append((number, 50.0))
                # Pick best
                if matches:
                    matches.sort(key=lambda x: x[1], reverse=True)
                    number, conf = matches[0]
                else:
                    number, conf = None, None
            except Exception as e:
                number, conf, matches = None, None, []
            # Log
            with open(log_path, 'a') as logf:
                logf.write(f"ANALYZE x={x} y={y} w={width} h={height} thresh={thresh} blur={blur} tess_cfg='{tess_cfg}' result={number} conf={conf}\n")
            # Track best
            if number is not None and (conf is not None and conf > best_conf):
                best_result = {
                    'number': number,
                    'confidence': conf,
                    'config': {
                        'threshold': thresh,
                        'blur': blur,
                        'tesseract_config': tess_cfg
                    },
                    'image': os.path.join(analyze_dir, img_filename)
                }
                best_conf = conf
            attempt += 1
        return best_result


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and analyze a cell from a Sudoku grid image')
    parser.add_argument('--image', required=True, help='Path to the input image')
    parser.add_argument('--x', type=int, required=True, help='X coordinate of the cell')
    parser.add_argument('--y', type=int, required=True, help='Y coordinate of the cell')
    parser.add_argument('--width', type=int, required=True, help='Width of the cell')
    parser.add_argument('--height', type=int, required=True, help='Height of the cell')
    parser.add_argument('--config', default='config/ocr_settings.yaml', help='Path to the configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    try:
        args = parser.parse_args()
        
        # Check if the image exists
        if not os.path.exists(args.image):
            print(f"Error: Image file not found: {args.image}")
            return 1
        
        # Check if the config file exists
        if not os.path.exists(args.config):
            print(f"Error: Configuration file not found: {args.config}")
            return 1
        
        # Load the image
        image = cv2.imread(args.image)
        if image is None:
            print(f"Error: Failed to load image: {args.image}")
            return 1
        
        # Create the cell extractor
        extractor = CellExtractor(config_path=args.config)
        
        # Extract the cell
        result = extractor.extract_cell(image, args.x, args.y, args.width, args.height)
        
        # Print the result
        print("Cell analysis result:")
        print(f"  Number: {result['number']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Confidence level: {result['confidence_level']}")
        print(f"  Has content: {result['has_content']}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())