import cv2
import numpy as np
import os
from pathlib import Path

def enhance_image(image):
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply gamma correction
    gamma = 0.5  # Adjust this value to control the gamma correction
    lookUpTable = np.empty((1,256), np.uint8)
    for i in range(256):
        lookUpTable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
    gamma_corrected = cv2.LUT(gray, lookUpTable)
    
    # Apply contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gamma_corrected)
    
    # Apply thresholding to get pure black and white
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def process_directory(input_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all PNG files in the input directory
    for png_file in Path(input_dir).glob('*.png'):
        # Read the image
        image = cv2.imread(str(png_file))
        if image is None:
            print(f"Failed to read {png_file}")
            continue
            
        # Enhance the image
        enhanced = enhance_image(image)
        
        # Save the enhanced image
        output_path = os.path.join(output_dir, png_file.name)
        cv2.imwrite(output_path, enhanced)
        print(f"Processed {png_file.name}")

if __name__ == "__main__":
    input_dir = "tests/png"
    output_dir = "tests/png_v2"
    process_directory(input_dir, output_dir) 