# Feature 1: Modular PDF to Sudoku Grid Extraction

## Directory Structure
```
.
├── pdf/                    # Input PDF files
├── logs/                   # All output files
│   ├── png/               # Extracted PNG files only
│   ├── analysis/          # JSON analysis files
│   ├── grids.txt          # Extracted Sudoku grids
│   └── grids_analysis.txt # Number recognition data
├── tests/                 # Test files
├── src/                   # Source code
└── config/               # Configuration files
    └── ocr_settings.yaml # OCR and cell processing settings
```

## Configuration

### ocr_settings.yaml
```yaml
# Cell Processing Settings
cell_padding: 0.1        # Padding around cell content (10% of cell size)
cell_border_width: 2     # Width of border to exclude from number reading
min_contour_area: 50     # Minimum area for a contour to be considered content
max_contour_area: 1000   # Maximum area for a contour to be considered content

# OCR Settings
tesseract_config: '--psm 10 --oem 3'  # Page segmentation mode and OCR engine mode
confidence_thresholds:
  high: 90    # High confidence threshold (>= 90%)
  medium: 50  # Medium confidence threshold (>= 50%)
  low: 0      # Low confidence threshold (>= 0%)

# Image Processing
preprocessing:
  blur_kernel_size: 3    # Size of Gaussian blur kernel
  threshold_value: 127   # Binary threshold value
  threshold_type: 'THRESH_BINARY_INV'  # Threshold type
  morph_kernel_size: 3   # Size of morphological operation kernel

# Debug Settings
save_debug_images: false  # Whether to save intermediate processing images
debug_output_dir: 'logs/debug'  # Directory for debug images
```

## Scripts and Their Responsibilities

### 1. pdf_grid_extractor.py
- **Purpose**: Extract Sudoku grids from PDF files and save as PNGs
- **Input**: PDF files from `pdf/` directory
- **Output**: PNG files in `logs/png/`
- **Parameters**:
  - `--clean`: Remove all existing PNG files before processing
  - `--limit_grids <number>`: Process only specified number of grids
- **Dependencies**: PyMuPDF (fitz), OpenCV, numpy

### 2. png_grid_extractor.py
- **Purpose**: Process PNG files to extract Sudoku grids and analyze numbers
- **Input**: PNG files from `logs/png/`
- **Output**: 
  - `logs/grids.txt`: Extracted Sudoku grids
  - `logs/grids_analysis.txt`: Number recognition data
  - `logs/analysis/grid*.json`: Individual grid analysis
- **Parameters**:
  - `--clean`: Remove all existing output files before processing
  - `--limit_grids <number>`: Process only specified number of grids
- **Dependencies**: extract_cell.py, OpenCV, pytesseract

### 3. extract_cell.py
- **Purpose**: Extract and analyze a single cell from a PNG image
- **Class**: `CellExtractor`
  ```python
  class CellExtractor:
      def __init__(self, config_path: str):
          """
          Initialize the cell extractor with configuration.
          
          Args:
              config_path: Path to the YAML configuration file
          """
          self.config = self._load_config(config_path)
          self._validate_config()
          
      def extract_cell(self, image_data: np.ndarray, x: int, y: int, width: int, height: int) -> dict:
          """
          Extract and analyze a cell from the image.
          
          Args:
              image_data: The source image as numpy array
              x, y: Top-left coordinates of the cell
              width, height: Dimensions of the cell
              
          Returns:
              Dictionary containing:
              - number: Recognized number or None
              - confidence: Confidence score (0-100) or None
              - confidence_level: 'high', 'medium', 'low', or 'failed'
              - has_content: Boolean indicating if cell contains any content
              - debug_info: Additional debug information if enabled
          """
  ```
- **Input**: 
  - PNG file path
  - Cell coordinates (x, y, width, height)
  - Configuration file path
- **Output**: 
  - Recognized number
  - Confidence score
  - Confidence level
  - Debug information (optional)
- **Dependencies**: 
  - OpenCV
  - pytesseract
  - PyYAML
  - numpy

## File Formats

### grids.txt
```
Grid 1:
+-------+-------+-------+
| - - - | 1 - - | - - - |
| 5 - - | 4 - - | - 8 9 |
| 9 8 1 | - - - | - 4 6 |
+-------+-------+-------+
| - 7 - | - 9 3 | - - 2 |
| 4 - - | 7 5 - | - 3 - |
| 3 - - | 2 - - | 8 - - |
+-------+-------+-------+
| - 9 - | - 2 8 | - - - |
| 6 5 - | - 7 - | - 2 - |
| - 1 - | 3 - - | 6 - - |
+-------+-------+-------+

Grid 2:
...
```

### grids_analysis.txt
```
Grid 1:
+----------+----------+----------+
| -- -- -- | 1h -- -- | -- -- -- |
| 5h -- -- | -- -- -- | -- 8h 9l |
| -- -- 1h | -- -- -- | -- -- 6h |
+----------+----------+----------+

Confidence Levels:
h = High confidence (>90%)
m = Medium confidence (50-90%)
l = Low confidence (<50%)
```

### grid*.json
```json
{
  "grid_number": 1,
  "source_file": "logs/png/grid1.png",
  "cells": [
    {
      "position": [0, 0],
      "number": null,
      "confidence": null
    },
    {
      "position": [0, 1],
      "number": "1",
      "confidence": 95.5
    }
  ],
  "statistics": {
    "total_cells": 81,
    "recognized_cells": 32,
    "average_confidence": 85.2
  }
}
```

## Test Requirements

### 1. Basic Tests
Each script should have basic tests that verify:
- Script runs without errors
- Output files are generated in correct locations
- Output files have correct format
- `--clean` parameter works
- `--limit_grids` parameter works

### 2. Test Structure
```
tests/
├── test_pdf_grid_extractor.py
├── test_png_grid_extractor.py
└── test_extract_cell.py
```

### 3. Test Data
- Create a `tests/data` directory with sample files
- Include a small PDF with known Sudoku grids
- Include sample PNG files for testing
- Include expected output files for comparison

## Implementation Guidelines

1. **Error Handling**
   - All scripts should handle errors gracefully
   - Log errors to appropriate log files
   - Provide meaningful error messages

2. **Logging**
   - Use Python's logging module
   - Log files should be in `logs/` directory
   - Include timestamps and log levels

3. **Code Organization**
   - Use classes for main functionality
   - Separate configuration from code
   - Use type hints
   - Include docstrings

4. **Performance**
   - Process files in parallel where possible
   - Use efficient image processing techniques
   - Implement proper cleanup of temporary files

5. **Documentation**
   - Include README.md for each script
   - Document all parameters
   - Include usage examples

6. **Configuration Management**
   - Use YAML for configuration files
   - Validate configuration on startup
   - Provide default values for all settings
   - Document all configuration options
   - Include example configurations

7. **Debug Support**
   - Enable/disable debug output via configuration
   - Save intermediate processing steps
   - Include detailed logging of processing steps
   - Generate visual debug output when enabled

## Integration Tests

### integration_test.py
- **Purpose**: Verify end-to-end functionality of the PDF to grid extraction pipeline
- **Functionality**:
  - Scan `pdf/` directory for matching PDF and TXT files
  - For each matching pair:
    1. Convert PDF to PNG using `pdf_grid_extractor.py`
    2. Extract grids from PNG using `png_grid_extractor.py`
    3. Compare extracted grids with expected grids from TXT files
  - Generate detailed comparison report
- **Output Format**:
  ```
  Testing: example.pdf
  ========================================
  Grid 1:
  Expected:                    Actual:
  +-------+-------+-------+    +-------+-------+-------+
  | 5 3 - | - 7 - | - - - |    | 5 3 - | - 7 - | - -!4 |
  | 6 - - | 1 9 5 | - - - |    | 6 - - | 1 9 5 | - - - |
  | - 9 8 | - - - | - 6 - |    | - 9 8 | - - - | -!- - |
  +-------+-------+-------+    +-------+-------+-------+
  | 8 - - | - 6 - | - - 3 |    |!1 - - | - 6 - | - - 3 |
  | 4 - - | 8 - 3 | - - 1 |    |!2 - - | 8 - 3 | - - 1 |
  | 7 - - | - 2 - | - - 6 |    | 7 - - | - 2 - | - - 6 |
  +-------+-------+-------+    +-------+-------+-------+
  | - 6 - | - - - | 2 8 - |    | - 6 - | - - - | 2 8 - |
  | - - - | 4 1 9 | - - 5 |    | - - - | 4!7 9 | - - 5 |
  | - - - | - 8 - | - 7 9 |    | - - - | - 8 - | - 7 9 |
  +-------+-------+-------+    +-------+-------+-------+
 

  Differences found: 2
  ========================================
  ```
- **Features**:
  - Side-by-side grid comparison
  - Visual indicators for differences (! prefix)
  - Summary of total differences per grid
  - Clear separation between different grids
  - Support for multiple grids per PDF
- **Dependencies**:
  - All core modules (pdf_grid_extractor.py, png_grid_extractor.py)
  - File comparison utilities
  - Grid formatting utilities
- **Error Handling**:
  - Skip files without matching pairs
  - Report missing files
  - Handle malformed grid files
  - Log processing errors

## Example Usage

```bash
# Extract grids from PDF
python pdf_grid_extractor.py --clean --limit_grids 2

# Process extracted PNGs
python png_grid_extractor.py --clean --limit_grids 2

# Extract single cell
python extract_cell.py --image logs/png/grid1.png --x 0 --y 0 --width 50 --height 50
```

## Testing Commands

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_pdf_grid_extractor.py

# Run with coverage
pytest --cov=src tests/
``` 