import os
import re
from pathlib import Path

LOG_FILE = 'logs/png_grid_extractor.log'
GRIDS_TXT = 'logs/grids.txt'
PNG_DIR = 'logs/png'
OUTPUT_HTML = 'logs/analysis.html'

# HTML templates
SCRIPT_TEMPLATE = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Hamburger menu logic
  const hamburger = document.getElementById('hamburger-menu');
  const navMenu = document.getElementById('file-nav-menu');
  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function(e) {
      e.stopPropagation();
      navMenu.classList.toggle('open');
      hamburger.classList.toggle('open');
    });
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!navMenu.contains(e.target) && !hamburger.contains(e.target)) {
        navMenu.classList.remove('open');
        hamburger.classList.remove('open');
      }
    });
  }

  // Update sudoku counter
  function updateCounter() {
    const counterArea = document.getElementById('sudoku-counter-area') || document.querySelector('.sudoku-count');
    const items = document.querySelectorAll('.item');
    let visibleCount = 0;
    items.forEach(item => {
      if (!item.classList.contains('hidden')) visibleCount++;
    });
    if (counterArea) {
      counterArea.textContent = 'Sudokus: ' + visibleCount;
    }
  }
  updateCounter();

  // Checkbox filter
  const checkbox = document.getElementById('hide-lowmed-checkbox') || document.getElementById('hide-high-checkbox');
  if (checkbox) {
    checkbox.addEventListener('change', function() {
      const items = document.querySelectorAll('.item');
      items.forEach(item => {
        if (!(item.classList.contains('low') || item.classList.contains('medium'))) {
          // Not low or medium
          if (checkbox.checked) {
            item.classList.add('hidden');
          } else {
            item.classList.remove('hidden');
          }
        } else {
          // Always show low/medium
          item.classList.remove('hidden');
        }
      });
      updateCounter();
    });
  }
});
</script>
'''

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{title}}</title>
    <style>
      body {
        font-family: monospace;
        margin: 0;
        padding: 0;
      }
      .navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        background: #222;
        color: #fff;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: flex-start;
        padding: 0.5em 2em 0.5em 2em;
        box-sizing: border-box;
        height: auto;
        overflow-x: auto;
      }
      .navbar-row {
        width: 100%;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 0.2em;
      }
      .navbar .counter-area, .navbar .sudoku-count {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1.2em;
        font-weight: bold;
        margin-right: 2em;
      }
      .hamburger {
        width: 2em;
        height: 2em;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        margin-right: 1em;
        z-index: 1100;
      }
      .hamburger-bar {
        width: 1.7em;
        height: 0.3em;
        background: #fff;
        margin: 0.18em 0;
        border-radius: 2px;
        transition: all 0.3s;
      }
      .hamburger.open .bar1 {
        transform: rotate(45deg) translate(0.35em, 0.35em);
      }
      .hamburger.open .bar2 {
        opacity: 0;
      }
      .hamburger.open .bar3 {
        transform: rotate(-45deg) translate(0.35em, -0.35em);
      }
      .file-nav-menu {
        display: none;
        position: absolute;
        top: 3.5em;
        left: 0;
        background: #222;
        color: #fff;
        width: 18em;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border-radius: 0 0 8px 0;
        padding: 0.5em 0.5em 0.5em 1em;
        z-index: 1200;
        flex-direction: column;
      }
      .file-nav-menu.open {
        display: flex;
      }
      .file-nav-menu .nav-link {
        display: block;
        color: #fff;
        text-decoration: none;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        padding: 0.3em 0.7em;
        border-radius: 4px;
        margin-bottom: 0.2em;
        transition: background 0.2s;
      }
      .file-nav-menu .nav-link:hover {
        background: #444;
      }
      .navbar .right-controls {
        display: flex;
        align-items: center;
        margin-left: auto;
      }
      .navbar label {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin-left: 0.5em;
        cursor: pointer;
      }
      .container {
        display: flex;
        flex-direction: column;
        flex-wrap: wrap;
        margin-top: 4.5em;
      }
      .item {
        width: 100%;
        margin-bottom: 32px;
        display: flex;
        flex-direction: column;
        transition: opacity 0.2s;
      }
      .item-content {
        display: flex;
        width: 100%;
        align-items: flex-start;
      }
      .left {
        width: 33%;
        padding: 8px;
        position: relative;
      }
      .middle {
        width: 33%;
        padding: 8px;
        white-space: pre;
      }
      .sudoku-pre {
        font-size: 2.1em;
        line-height: 1.1;
        margin: 0;
        font-family: inherit;
      }
      .right {
        width: 34%;
        padding: 8px;
        white-space: pre;
        word-break: break-all;
      }
      .sudoku-counter {
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 4px;
      }
      .logline {
        color: #000;
      }
      .reliability-low, .low {
        color: #a00;
      }
      .reliability-medium, .medium {
        color: orange;
      }
      .reliability-high {
        color: #000;
      }
      .high {
        color: #006400;
        font-weight: bold;
      }
      .sudoku-img {
        max-width: 22rem;
        max-height: 22rem;
        width: auto;
        height: auto;
        display: block;
        position: relative;
      }
      h2.item-title {
        width: 100%;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 8px;
        font-family: Arial, Helvetica, sans-serif;
        display: block;
      }
      .empty {
        opacity: 0.5;
      }
      .hidden {
        display: none !important;
      }
      /* Highlight items with medium/low reliability */
      .item.medium {
        border-left: 8px solid orange;
        background: #fffbe6;
      }
      .item.low {
        border-left: 8px solid #a00;
        background: #fff0f0;
      }
    </style>
    {{script_block}}
  </head>
  <body>
    <div class="navbar">
      <div class="navbar-row">
        <span class="sudoku-count" id="sudoku-counter-area">Sudokus: ...</span>
        <div class="hamburger" id="hamburger-menu" tabindex="0" aria-label="Toggle file navigation" role="button">
          <div class="hamburger-bar bar1"></div>
          <div class="hamburger-bar bar2"></div>
          <div class="hamburger-bar bar3"></div>
        </div>
      </div>
      <div class="navbar-row">
        <span class="right-controls">
          <input type="checkbox" id="hide-lowmed-checkbox">
          <label for="hide-lowmed-checkbox">Hide low/medium reliability</label>
        </span>
      </div>
      <div class="file-nav-menu" id="file-nav-menu">
        {{navbar_links}}
      </div>
    </div>
    <div class="container">
      {{content}}
    </div>
  </body>
</html>
'''

ITEM_TEMPLATE = '''
<div class="item{{item_classes}}">
  <h2 class="item-title">
    <span class="sudoku-counter">Sudoku {{idx}}</span> &mdash; {{basename}}
  </h2>
  <div class="item-content">
    <div class="left" style="position:relative;display:inline-block;vertical-align:top;">
      <img src="{{rel_png_path}}" class="sudoku-img">
    </div>
    <div class="middle"><pre class="sudoku-pre">{{grid_txt}}</pre></div>
    <div class="right"><pre class="sudoku-pre">{{reliability_grid}}</pre></div>
  </div>
</div>
'''

LOG_LINE_TEMPLATE = '<div class="logline {reliability_class}">{logline}</div>'

# Parse grids.txt to map grid names to their text representation
def parse_grids_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    grids = {}
    current_name = None
    current_grid = []
    current_file = None
    for line in lines:
        line = line.rstrip('\n')
        if line.startswith('Source file: '):
            current_file = line[len('Source file: '):]
        elif line.startswith('Ruudukko: '):
            if current_file and current_grid:
                grids[current_file] = '\n'.join(current_grid)
            current_name = line[len('Ruudukko: '):]
            current_grid = []
        elif line.strip() == '' and current_file and current_grid:
            grids[current_file] = '\n'.join(current_grid)
            current_file = None
            current_grid = []
        elif current_file is not None:
            current_grid.append(line)
    if current_file and current_grid:
        grids[current_file] = '\n'.join(current_grid)
    return grids

# Find all PNG files referenced in the log file
def get_png_files_from_log(log_path):
    png_files = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'Processing (logs/png/[^.]+\.png)', line)
            if m:
                png_files.append(m.group(1))
    return png_files

def parse_cell_logs(log_path):
    """Return a dict: {png_file: [ {x, y, w, h, reliability, logline}, ... ] }"""
    cell_data = {}
    current_png = None
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            m_proc = re.search(r'Processing (logs/png/[^.]+\.png)', line)
            if m_proc:
                current_png = m_proc.group(1)
                continue
            m_cell = re.search(r'Cell \(\d+,\d+\) at \(x=(\d+), y=(\d+), w=(\d+), h=(\d+)\): (.+)', line)
            if m_cell and current_png:
                x, y, w, h, rest = m_cell.groups()
                reliability = None
                m_rel = re.search(r'reliability=(\w+)', rest)
                if m_rel:
                    reliability = m_rel.group(1)
                entry = {
                    'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h),
                    'reliability': reliability, 'logline': line.strip()
                }
                cell_data.setdefault(current_png, []).append(entry)
    return cell_data

def extract_reliability_grid(grid_txt, cell_logs):
    grid_lines = [line for line in grid_txt.split('\n') if line.startswith('|')]
    grid_cells = []
    for line in grid_lines:
        cells = [c.strip() for c in line.strip('|').split('|')]
        row = []
        for cell in cells:
            row.extend(cell.split())
        grid_cells.append(row)
    reliability_grid = [['-' for _ in range(9)] for _ in range(9)]
    idx = 0
    has_medium = False
    has_low = False
    for row in range(9):
        for col in range(9):
            if idx < len(cell_logs):
                rel = cell_logs[idx].get('reliability', 'high')
                if rel == 'high':
                    reliability_grid[row][col] = '<span class="high">H</span>'
                elif rel == 'medium':
                    reliability_grid[row][col] = '<span class="medium">M</span>'
                    has_medium = True
                elif rel == 'low':
                    reliability_grid[row][col] = '<span class="low">L</span>'
                    has_low = True
                else:
                    reliability_grid[row][col] = '<span class="empty">-</span>'
            else:
                reliability_grid[row][col] = '<span class="empty">-</span>'
            idx += 1
    out_lines = []
    grid_line_idx = 0
    for line in grid_txt.split('\n'):
        if line.startswith('|'):
            row = reliability_grid[grid_line_idx]
            parts = [c.strip() for c in line.strip('|').split('|')]
            new_parts = []
            cell_idx = 0
            for part in parts:
                cell_count = len(part.split())
                rels = row[cell_idx:cell_idx+cell_count]
                new_parts.append(' '.join(rels))
                cell_idx += cell_count
            out_lines.append('| ' + ' | '.join(new_parts) + ' |')
            grid_line_idx += 1
        else:
            out_lines.append(line)
    # Return the bordered grid and the flags for medium/low
    return '\n'.join(out_lines), has_medium, has_low

def get_sudoku_prefix(filename):
    # Extracts the prefix before _p<pagenumber>_g<gridnumber>.png
    m = re.match(r'(.+)_p\d+_g\d+\.png', filename)
    if m:
        return m.group(1)
    return filename

def main():
    grids = parse_grids_txt(GRIDS_TXT)
    png_files = get_png_files_from_log(LOG_FILE)
    cell_logs = parse_cell_logs(LOG_FILE)
    seen = set()
    unique_png_files = []
    for f in png_files:
        if f not in seen:
            unique_png_files.append(f)
            seen.add(f)
    # Collect unique prefixes and their first index
    prefix_to_index = {}
    prefix_to_label = {}
    for idx, png_file in enumerate(unique_png_files):
        prefix = get_sudoku_prefix(os.path.basename(png_file))
        if prefix not in prefix_to_index:
            prefix_to_index[prefix] = idx
            prefix_to_label[prefix] = os.path.basename(png_file).split('_p')[0]
    # Build HTML content
    items_html = []
    for idx, png_file in enumerate(unique_png_files):
        rel_png_path = os.path.relpath(png_file, os.path.dirname(OUTPUT_HTML))
        grid_txt = grids.get(png_file, '<span style="color:red">Grid not found in grids.txt</span>')
        reliability_grid = ''
        item_classes = ''
        prefix = get_sudoku_prefix(os.path.basename(png_file))
        # Add anchor before the first sudoku of each prefix group
        if prefix_to_index[prefix] == idx:
            anchor = f'<a id="prefix-{prefix}"></a>'
            items_html.append(anchor)
        if png_file in grids and png_file in cell_logs:
            reliability_grid_str, has_medium, has_low = extract_reliability_grid(grid_txt, cell_logs[png_file])
            reliability_grid = reliability_grid_str
            if has_low:
                item_classes = ' low'
            elif has_medium:
                item_classes = ' medium'
            else:
                item_classes = ' high'
        else:
            reliability_grid = '<span style="color:red">No reliability data</span>'
            item_classes = ''
        item_html = ITEM_TEMPLATE.replace('{{idx}}', str(idx+1)) \
                                   .replace('{{basename}}', os.path.basename(png_file)) \
                                   .replace('{{rel_png_path}}', rel_png_path) \
                                   .replace('{{grid_txt}}', grid_txt) \
                                   .replace('{{reliability_grid}}', reliability_grid) \
                                   .replace('{{item_classes}}', item_classes)
        items_html.append(item_html)
        if idx + 1 < len(unique_png_files):
            this_prefix = get_sudoku_prefix(os.path.basename(png_file))
            next_prefix = get_sudoku_prefix(os.path.basename(unique_png_files[idx+1]))
            if this_prefix != next_prefix:
                items_html.append('<div style="height:10em"></div>')
    # Build navbar links for prefixes
    navbar_links = []
    for prefix, idx in prefix_to_index.items():
        # Shorten label: just the last part after last slash or concise
        label = os.path.basename(prefix_to_label[prefix])
        navbar_links.append(f'<a href="#prefix-{prefix}" class="nav-link">{label}</a>')
    navbar_links_html = ' '.join(navbar_links)
    # Insert navbar_links_html into the navbar
    final_html = HTML_TEMPLATE.replace('{{title}}', 'Sudoku Grid Analysis') \
                              .replace('{{content}}', ''.join(items_html)) \
                              .replace('{{sudoku_count}}', str(len(unique_png_files))) \
                              .replace('{{navbar_links}}', navbar_links_html) \
                              .replace('{{script_block}}', SCRIPT_TEMPLATE)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Analysis HTML written to {OUTPUT_HTML}")

if __name__ == '__main__':
    main() 