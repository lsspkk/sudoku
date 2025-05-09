# Sudoku Solver 

Contains a sudoku solver with logic engineered by kids.

And an AI-engineered tool for extracting Sudoku grids from PDF files and recognizing numbers using OCR.

There are also a few documented AI failures, because the grid extractor tool was made with vibe coding.


## Features

- Extract pages from PDF files as PNG images
- Detect Sudoku grids in PNG images
- Extract and recognize numbers from Sudoku grid cells
- Generate grid output in text format
- Detailed confidence analysis for number recognition


## Usage


```
python3 src/pdf_grid_extractor.py
python3 src/whiten_pngs.py logs/png
```

This will process all .pdf files in the pdf/ directory and save the extracted PNG grids to logs/png/. Make white areas actually white pixels, clear of slightly grey dots.


### Extracting text grids from PNG files

To extract Sudoku grids from a file or all PNG files in a folder (e.g., logs/png), run:

```
python3 src/png_grid_extractor.py logs/png
```



## Directory Structure

```
.
├── ai_failures/                # (no explanation)
│   └── ...
├── data/                       # Digit template images
│   ├── 1.png
│   ├── 2.png
│   └── ...
├── logs/                       # All output files
│   ├── grids.txt
│   ├── png_grid_extractor.log
│   ├── pdf_grid_extractor.log
│   ├── diff.txt
│   ├── png/                    # Extracted PNG files
│   │   └── ...
├── pdf/                        # Input PDF files
│   └── ...
├── src/                        # Source code
│   ├── analyze_logs.py         # Analysis and HTML reporting
│   ├── analyze.js              # JS for HTML analysis interactivity
│   ├── cell_extract.py         # Cell-level image processing and OCR
│   ├── diff.py                 # Diff utilities
│   ├── ocr_config.yaml         # OCR configuration
│   ├── pdf_grid_extractor.py   # Extracts Sudoku grids from PDFs
│   ├── png_grid_extractor.py   # Extracts Sudoku grids from PNGs
│   ├── ratkaisija.py           # Sudoku solver
│   ├── whiten_pngs.py          # PNG whitening utility
├── tests/                      # Test files and data
│   └── ...
├── README.md
├── requirements.txt
└── ...
```

## Installation

1. Clone the repository
2. Create a venv and install the dependencies with pip
3. Ensure you have Tesseract OCR installed on your system.


## Configuration

The OCR and image processing settings can be configured in `src/ocr_config.yaml`.
Settings were created by first manually creating some grids.
Then, tests were run that showed cells with poor OCR reliability.
These cells were extracted into images and tested using `tests/compare_cells.py`.
From statistics, the OCR methods were chosen that produced correct answers.



## License

This project is licensed under the MIT License - see the LICENSE file for details.
