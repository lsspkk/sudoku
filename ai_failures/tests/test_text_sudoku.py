import sys
from pathlib import Path

# Add parent directory to Python path to import text_sudoku
sys.path.append(str(Path(__file__).parent.parent))

from text_sudoku import add_confidence_levels

def test_horizontal_line_length():
    # Create test data - a realistic Sudoku grid with various confidence levels
    grid = [
        ['1', '--', '3', '4', '-', '6', '7', '--', '9'],
        ['--', '2', '--', '--', '5', '--', '--', '8', '--'],
        ['7', '--', '9', '1', '-', '3', '--', '--', '6'],
        ['--', '--', '--', '--', '--', '--', '--', '--', '--'],
        ['3', '1', '--', '7', '2', '8', '-', '4', '5'],
        ['--', '--', '--', '--', '--', '--', '--', '--', '--'],
        ['5', '--', '7', '3', '-', '2', '8', '--', '1'],
        ['--', '3', '--', '--', '7', '--', '--', '5', '--'],
        ['2', '--', '1', '8', '-', '4', '3', '--', '7']
    ]
    
    # Confidence levels matching the grid
    confidence_grid = [
        ['H', 'F', 'H', 'H', 'F', 'M', 'H', 'F', 'H'],
        ['F', 'H', 'F', 'F', 'H', 'F', 'F', 'H', 'F'],
        ['H', 'F', 'H', 'H', 'F', 'H', 'F', 'F', 'H'],
        ['F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F'],
        ['H', 'H', 'F', 'H', 'H', 'H', 'F', 'H', 'H'],
        ['F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F'],
        ['H', 'F', 'H', 'H', 'F', 'H', 'H', 'F', 'H'],
        ['F', 'H', 'F', 'F', 'H', 'F', 'F', 'M', 'F'],
        ['H', 'F', 'H', 'H', 'F', 'H', 'L', 'F', 'H']
    ]
    
    # Get formatted output
    result = add_confidence_levels(grid, confidence_grid, cell_width=2)
    
    # Split into lines
    lines = result.split('\n')
    
    # Check horizontal line length
    # Each cell block (3 cells) has:
    # - 3 cells * (2 chars + 1 confidence char) = 9 chars
    # - Plus 1 space for padding = 10 chars
    # Total line: + + 3 blocks of 10 chars + 2 additional + = 34 chars
    expected_length = 34
    horizontal_lines = [line for line in lines if line.startswith('+')]
    
    for line in horizontal_lines:
        assert len(line) == expected_length, \
            f"Horizontal line length is {len(line)}, expected {expected_length}\nLine: {line}"
    
    print("All horizontal lines have correct length!")
    print("\nTest output:")
    print(result)

if __name__ == "__main__":
    test_horizontal_line_length() 