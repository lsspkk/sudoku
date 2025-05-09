import cv2
import pytesseract
import numpy as np

def extract_number_from_cell_data(cell_image_data):
    """
    Extracts a number from the provided image data of a single Sudoku cell.

    Args:
        cell_image_data: A NumPy array representing the image data for the cell.

    Returns:
        A tuple containing:
            - The recognized digit as a string ('1' through '9'), or an empty string if no digit is found.
            - The confidence level (float) reported by Tesseract, or -1 if no text or confidence is found.
    """
    # Ensure the input is a NumPy array
    if not isinstance(cell_image_data, np.ndarray):
        raise TypeError("Input must be a NumPy array representing image data.")

    # Ensure it's grayscale. If it has 3 channels, convert it.
    if len(cell_image_data.shape) == 3 and cell_image_data.shape[2] == 3:
        gray = cv2.cvtColor(cell_image_data, cv2.COLOR_BGR2GRAY)
    elif len(cell_image_data.shape) == 2:
        gray = cell_image_data.copy() # Already grayscale
    else:
        # Handle unexpected shapes (e.g., 4 channels RGBA or other)
        # For simplicity, try converting if possible, otherwise raise error
        try:
            gray = cv2.cvtColor(cell_image_data, cv2.COLOR_BGRA2GRAY) # Attempt common conversions
        except cv2.error:
             raise ValueError(f"Unsupported image shape for grayscale conversion: {cell_image_data.shape}")


    # --- OCR Configuration ---
    # psm 10: Treat the image as a single character.
    # oem 3: Use LSTM OCR Engine only.
    # tessedit_char_whitelist: Only recognize digits 1-9.
    ocr_config = '--psm 10 --oem 3 -c tessedit_char_whitelist=123456789'

    # --- Recognize Digit ---
    digit = pytesseract.image_to_string(gray, config=ocr_config).strip()

    # --- Get Confidence Score ---
    # Use image_to_data to get detailed information including confidence
    data = pytesseract.image_to_data(
        gray,
        config=ocr_config,
        output_type=pytesseract.Output.DICT
    )

    confidence = -1.0 # Default: indicates no confidence score found

    # Iterate through detected text blocks to find the confidence
    # We expect only one block due to psm 10, but iterate for robustness
    for i, text in enumerate(data['text']):
        if text: # Found a recognized text block
            try:
                # Tesseract returns confidence as a string, potentially '-1'
                conf_val = data['conf'][i]
                # Convert to float, handle potential '-1' string or other non-numeric values
                parsed_conf = float(conf_val)
                if parsed_conf >= 0: # Valid confidence scores are 0-100
                     confidence = parsed_conf
                # If parsed_conf is -1, confidence remains the default -1.0
            except (ValueError, IndexError):
                # Handle errors during conversion or if index is out of bounds
                pass # Confidence remains -1.0
            break # Stop after processing the first detected text block

    # Return the digit (if found) and the confidence score
    return digit if digit else '', confidence

if __name__ == '__main__':
    # Example of how to use this function (requires a sample cell image)
    # Create a dummy black image with a white digit '5' for testing
    dummy_cell = np.zeros((50, 50), dtype=np.uint8) # Black background
    cv2.putText(dummy_cell, '5', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255), 2) # White '5'

    # Save dummy image to test file not found error (optional)
    # cv2.imwrite("dummy_cell.png", dummy_cell)

    try:
        # Test with dummy data
        number, conf = extract_number_from_cell_data(dummy_cell)
        print(f"[Test] Recognized number: '{number}', Confidence: {conf:.2f}")

        # Example: Test with a non-image input
        # extract_number_from_cell_data("not an image")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except TypeError as e:
        print(f"Error: {e}")
    except ValueError as e:
         print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 