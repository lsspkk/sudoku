import re

def parse_diff_cells(diff_path):
    mismatches = []
    with open(diff_path, 'r') as f:
        lines = f.readlines()
    grid_num = None
    row_idx = 0
    for line in lines:
        grid_match = re.match(r"Grid (\d+) cell-by-cell comparison:", line)
        if grid_match:
            grid_num = int(grid_match.group(1))
            row_idx = 0
            continue
        if line.strip() == '' or grid_num is None:
            continue
        # Each cell is 7 chars wide
        cells = [line[i:i+7].strip() for i in range(0, len(line), 7)]
        for col_idx, cell in enumerate(cells):
            # Look for e.g. 1=4 ! (with optional whitespace before !)
            m = re.match(r"(.?)=(.?)\s*!", cell)
            if m:
                expected, actual = m.group(1).strip(), m.group(2).strip()
                mismatches.append({
                    'grid': grid_num,
                    'row': row_idx,
                    'col': col_idx,
                    'expected': expected,
                    'actual': actual
                })
        row_idx += 1
    return mismatches

def find_log_lines(log_path, mismatches):
    log_lines = []
    with open(log_path, 'r') as f:
        logs = f.readlines()
    for m in mismatches:
        # Look for a log line for this cell (row,col) in this grid
        # The log file does not have grid number, so just match cell (row,col)
        cell_pat = f"Cell ({m['row']},{m['col']})"
        found = None
        for line in logs:
            if cell_pat in line:
                found = line.strip()
                break
        log_lines.append({**m, 'log': found or '(no log found)'})
    return log_lines

def main():
    diff_path = 'logs/diff.txt'
    log_path = 'logs/png_grid_extractor.log'
    mismatches = parse_diff_cells(diff_path)
    log_lines = find_log_lines(log_path, mismatches)
    for entry in log_lines:
        print(f"Grid {entry['grid']} Cell ({entry['row']},{entry['col']}): expected '{entry['expected']}', actual '{entry['actual']}' | {entry['log']}")

if __name__ == '__main__':
    main() 