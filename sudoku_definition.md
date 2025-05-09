# Sudoku Text Format Definition

## Overview
The Sudoku text format is a simple text-based representation of a 9x9 Sudoku grid. It uses numbers 1-9 for filled cells and hyphens (-) for empty cells.

---

## Format Without Borders

### Format Rules
1. The grid is represented as 9 lines of text
2. Each line contains 9 space-separated values
3. Values can be:
   - Numbers 1-9 for filled cells
   - Hyphen (-) for empty cells
4. Lines can be separated by blank lines (they will be ignored)
5. Leading and trailing whitespace is ignored

### Example
```
7 - 4 5 - - 3 - -
9 - 6 7 - - - - 2 
2 1 - 6 9 - - - - 
- 6 - 4 - 5 - 3 9
- 7 8 - - - - - - 
- 3 - - - - 2 4 -
- - - - - - - - 8
8 2 7 1 - 9 5 - - 
- - - - - - - 1 - 
```

---

## Format With Borders

### Format Rules
1. The grid is represented as a bordered table, with rows and columns separated by vertical bars (|) and horizontal lines (+-------+-------+-------+)
2. Each cell contains either:
   - Numbers 1-9 for filled cells
   - Hyphen (-) for empty cells
3. The grid may be preceded by metadata lines, such as filename and title
4. The grid is always 9x9, grouped into 3x3 blocks

### Example
Filename: logs/png/easy_sudoku_booklet_1_fi_4_p1_g3.png
Title: easy_sudoku_booklet_1_fi_4, sivu 1 - numero 3

```
Source file: logs/png/easy_sudoku_booklet_1_fi_4_p1_g3.png
Ruudukko: easy_sudoku_booklet_1_fi_4, sivu 1 - numero 3
+-------+-------+-------+
| 7 - - | 4 - - | - - 5 |
| 8 6 - | 7 - - | - - - |
| 3 - - | 9 - 2 | - - - |
+-------+-------+-------+
| - - - | 3 - - | - 8 1 |
| 1 - 9 | - - - | 6 3 2 |
| - 4 - | 8 1 6 | - 5 - |
+-------+-------+-------+
| 9 3 - | 2 8 5 | 7 - - |
| 5 - - | - 4 7 | 1 - - |
| 4 - - | - - - | - - - |
+-------+-------+-------+
```

---

## Coordinate System
- The grid uses a 0-based coordinate system
- (0,0) is at the top-left corner
- x increases from left to right (columns)
- y increases from top to bottom (rows)

## Validation Rules
1. Each row must contain numbers 1-9 exactly once
2. Each column must contain numbers 1-9 exactly once
3. Each 3x3 box must contain numbers 1-9 exactly once
4. Empty cells are represented by "-"
5. The grid must be exactly 9x9

## Usage in Code
The format is used in the `lue_ruudukko()` function which:
1. Splits the input by lines
2. Ignores empty lines
3. Splits each line by spaces
4. Converts "-" to `TYHJA` constant
5. Converts numbers to integers
6. Returns a 2D list representation of the grid 