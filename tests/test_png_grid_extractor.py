import os
import subprocess

def test_png_grid_extractor():
    # Run the extractor
    result = subprocess.run(['python3', 'src/png_grid_extractor.py', 'tests/png'], capture_output=True, text=True)
    assert result.returncode == 0, f"Extractor failed: {result.stderr}"
    # Compare output
    with open('logs/grids.txt', 'r') as f:
        actual = f.read().strip()
    with open('tests/grids_expected.txt', 'r') as f:
        expected = f.read().strip()
    if actual != expected:
        print('DIFF:')
        import difflib
        for line in difflib.unified_diff(expected.splitlines(), actual.splitlines(), fromfile='expected', tofile='actual'):
            print(line)
        # Cell-by-cell comparison
        def parse_grids(txt):
            grids = []
            grid = []
            for line in txt.splitlines():
                line = line.strip()
                if line.startswith('Grid'):
                    if grid:
                        grids.append(grid)
                        grid = []
                elif line.startswith('|'):
                    cells = [c for c in line[1:-1].split('|')]
                    row = []
                    for block in cells:
                        row += [x for x in block.strip().split(' ') if x]
                    if row:
                        grid.append(row)
            if grid:
                grids.append(grid)
            return grids
        expected_grids = parse_grids(expected)
        actual_grids = parse_grids(actual)
        for gidx, (eg, ag) in enumerate(zip(expected_grids, actual_grids)):
            print(f"Grid {gidx+1} cell-by-cell comparison:")
            for row_e, row_a in zip(eg, ag):
                line = ''
                for ce, ca in zip(row_e, row_a):
                    mark = '!' if ce != ca else ''
                    cell_str = f"{ce:>2}={ca:<2}{mark}"
                    line += cell_str.ljust(7)
                print(line)
            print()
    assert actual == expected, "Output grids.txt does not match expected output. See diff and cell-by-cell comparison above."
    # Always run diff.py to update logs/diff.txt
    subprocess.run(['python3', 'src/diff.py'])
