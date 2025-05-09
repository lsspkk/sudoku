import difflib
import os

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

def main():
    # Clear diff.txt at start
    with open('logs/diff.txt', 'w') as diff_file:
        pass
    with open('logs/grids.txt', 'r') as f:
        actual = f.read().strip()
    with open('tests/grids_expected.txt', 'r') as f:
        expected = f.read().strip()
    diff_lines = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), fromfile='expected', tofile='actual'))
    if actual != expected:
        print('DIFF (see logs/diff.txt for details):')
        with open('logs/diff.txt', 'a') as diff_file:
            for line in diff_lines:
                diff_file.write(line + '\n')
            expected_grids = parse_grids(expected)
            actual_grids = parse_grids(actual)
            for gidx, (eg, ag) in enumerate(zip(expected_grids, actual_grids)):
                header = f"Grid {gidx+1} cell-by-cell comparison:"
                print(header)
                diff_file.write(header + '\n')
                for row_e, row_a in zip(eg, ag):
                    line = ''
                    for ce, ca in zip(row_e, row_a):
                        mark = '!' if ce != ca else ''
                        cell_str = f"{ce:>2}={ca:<2}{mark}"
                        # Pad to fixed width (7 chars)
                        line += cell_str.ljust(7)
                    print(line)
                    diff_file.write(line + '\n')
                print()
                diff_file.write('\n')
    else:
        print("No differences found. All grids match.")
        # Clear diff.txt if no differences
        with open('logs/diff.txt', 'w') as diff_file:
            diff_file.write('')

if __name__ == '__main__':
    main() 