from ratkaisija import viivoita_ruudukko
import json
from syottaja import Sudoku

json_tiedosto = "logs/ratkaisut.json"
html_tiedosto = "logs/sudokut.html"



CSS = '''
body {
  font-family: monospace;
  margin: 0;
  padding: 0;
  background: #f8f8f8;
  display: flex;
}
.side-menu {
  position: fixed;
  top: 0;
  left: 0;
  width: 260px;
  height: 100vh;
  background: #222;
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 2em 1.2em 1em 1.2em;
  box-sizing: border-box;
  z-index: 100;
  box-shadow: 2px 0 8px rgba(0,0,0,0.08);
  transition: left 0.3s, opacity 0.3s;
}
.side-menu.menu-hidden {
  left: -300px;
  opacity: 0;
  pointer-events: none;
}
#show-menu-btn {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 200;
  background: #222;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-family: Arial, Helvetica, sans-serif;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  display: none;
}
#show-menu-btn.menu-show {
  display: block;
}
@media print {
  .side-menu, #show-menu-btn {
    display: none !important;
  }
}
.side-menu h2 {
  font-size: 1.2em;
  margin-bottom: 1.2em;
  font-family: Arial, Helvetica, sans-serif;
  font-weight: bold;
  color: #fff;
}
.side-menu label, .side-menu input, .side-menu select, .side-menu button {
  font-family: inherit;
  font-size: 1em;
  margin-bottom: 0.7em;
  display: block;
  width: 100%;
}
.side-menu input[type="text"] {
  padding: 0.4em;
  border-radius: 4px;
  border: none;
  margin-bottom: 1em;
}
.side-menu select, .side-menu button, .side-menu input[type="checkbox"] {
  padding: 0.4em;
  border-radius: 4px;
  border: none;
  background: #444;
  color: #fff;
  margin-bottom: 1em;
  cursor: pointer;
}
.side-menu button:hover {
  background: #666;
}
.main-content {
  margin-left: 260px;
  width: 100%;
  box-sizing: border-box;
}
.container {
  display: flex;
  flex-direction: column;
  gap: 2em;
  margin: 2em auto;
  max-width: 1200px;
}
.sudoku-row {
  display: flex;
  flex-direction: row;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  overflow: hidden;
  align-items: flex-start;
  position: relative;
}
.sudoku-select {
  position: absolute;
  left: 0.7em;
  top: 0.7em;
  z-index: 2;
  transform: scale(1.3);
}
.sudoku-col {
  flex: 1 1 0;
  padding: 1.5em 1em 1.5em 2.5em;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}
.first-col {}
.second-col {}
.print-layout-hide .sudoku-pre {
  display: none !important;
}
.print-layout-size .sudoku-img-wrapper .sudoku-img {
  max-width: 30vw !important;
  max-height: 30vw !important;
  width: auto;
  height: auto;
}
.sudoku-title {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 1.1em;
  font-weight: bold;
  margin-bottom: 0.7em;
  color: #333;
}
pre.sudoku-pre {
  font-size: 1.3em;
  line-height: 1.15;
  margin: 0;
  background: #f4f4f4;
  border-radius: 4px;
  padding: 0.7em 1em;
  overflow-x: auto;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.sudoku-img-wrapper {
  margin-top: 0.5em;
  margin-bottom: 0.2em;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
.sudoku-img {
  max-width: 32px;
  max-height: 32px;
  width: auto;
  height: auto;
  border-radius: 3px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.07);
  background: #fff;
  display: block;
  transition: max-width 0.3s, max-height 0.3s;
}
'''

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Sudoku Solutions</title>
    <style>
    {{CSS}}
    </style>
    <script>
    function sortSudokusByLisaykset() {
      const order = document.getElementById('sort-lisaykset').value;
      const container = document.querySelector('.container');
      const sudokus = Array.from(container.querySelectorAll('.sudoku-row'));
      sudokus.sort((a, b) => {
        const aVal = parseInt(a.getAttribute('data-ratkaisun_kierrokset'));
        const bVal = parseInt(b.getAttribute('data-ratkaisun_kierrokset'));
        return order === 'asc' ? aVal - bVal : bVal - aVal;
      });
      sudokus.forEach(sudoku => container.appendChild(sudoku));
    }
    function filterSolvedSudokus() {
      const filter = document.getElementById('filter-valmis').value;
      document.querySelectorAll('.sudoku-row').forEach(row => {
        if (filter === 'all') {
          row.style.display = '';
        } else if (filter === 'solved') {
          row.style.display = row.getAttribute('data-valmis') === 'True' ? '' : 'none';
        } else if (filter === 'unsolved') {
          row.style.display = row.getAttribute('data-valmis') === 'False' ? '' : 'none';
        }
      });
    }
    function filterByNimi() {
      const substring = document.getElementById('filter-nimi').value;
      document.querySelectorAll('.sudoku-row').forEach(row => {
        if (!row.getAttribute('data-nimi').toLowerCase().includes(substring.toLowerCase())) {
          row.style.display = 'none';
        } else {
          row.style.display = '';
        }
      });
    }
    function filterBySelected() {
      const showSelected = document.getElementById('filter-selected').checked;
      document.querySelectorAll('.sudoku-row').forEach(row => {
        const checkbox = row.querySelector('.sudoku-select');
        if (showSelected && !checkbox.checked) {
          row.style.display = 'none';
        } else if (!showSelected && row.style.display === 'none-selected') {
          row.style.display = '';
        }
      });
    }
    function applyAllFilters() {
      // First, show all
      document.querySelectorAll('.sudoku-row').forEach(row => row.style.display = '');
      filterSolvedSudokus();
      filterByNimi();
      if (document.getElementById('filter-selected').checked) {
        document.querySelectorAll('.sudoku-row').forEach(row => {
          const checkbox = row.querySelector('.sudoku-select');
          if (!checkbox.checked) {
            row.style.display = 'none';
          }
        });
      }
      sortSudokusByLisaykset();
    }
    function togglePrintLayout() {
      const enabled = document.getElementById('toggle-print-layout').checked;

      document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (enabled ) {
          cb.classList.add('print-layout-hide');
        } else {
          cb.classList.remove('print-layout-hide');
        }
      });
      document.querySelectorAll('.first-col').forEach(col => {
        if (enabled) {
          col.classList.add('print-layout-hide');
          col.classList.add('print-layout-size');
        } else {
          col.classList.remove('print-layout-hide');
          col.classList.remove('print-layout-size');
        }
      });
      // Hide menu and show button if print layout is enabled
      const menu = document.querySelector('.side-menu');
      const showBtn = document.getElementById('show-menu-btn');
      if (enabled) {
        menu.classList.add('menu-hidden');
        showBtn.classList.add('menu-show');
      } else {
        menu.classList.remove('menu-hidden');
        showBtn.classList.remove('menu-show');
      }
    }
    function showMenu() {
      document.querySelector('.side-menu').classList.remove('menu-hidden');
      document.getElementById('show-menu-btn').classList.remove('menu-show');
      // Uncheck print layout if menu is shown
      document.getElementById('toggle-print-layout').checked = false;
      togglePrintLayout();
    }
    // Attach listeners on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
      document.getElementById('sort-lisaykset').addEventListener('change', applyAllFilters);
      document.getElementById('filter-valmis').addEventListener('change', applyAllFilters);
      document.getElementById('filter-nimi').addEventListener('input', applyAllFilters);
      document.getElementById('filter-selected').addEventListener('change', applyAllFilters);
      document.getElementById('toggle-print-layout').addEventListener('change', togglePrintLayout);
      document.getElementById('show-menu-btn').addEventListener('click', showMenu);
      document.querySelectorAll('.sudoku-select').forEach(cb => {
        cb.addEventListener('change', applyAllFilters);
      });
    });
    </script>
  </head>
  <body>
    <button id="show-menu-btn">Näytä menu</button>
    <div class="side-menu">
      <h2>Sort & Filter</h2>
      <label for="sort-lisaykset">Sort by numbers placed:</label>
      <select id="sort-lisaykset">
        <option value="asc">Ascending</option>
        <option value="desc">Descending</option>
      </select>
      <label for="filter-valmis">Show:</label>
      <select id="filter-valmis">
        <option value="all">All</option>
        <option value="solved">Only solved</option>
        <option value="unsolved">Only unsolved</option>
      </select>
      <label for="filter-nimi">Filter by name:</label>
      <input type="text" id="filter-nimi" placeholder="Type name..." />
      <label for="filter-selected" style="margin-top:1.2em;display:flex;align-items:center;gap:0.5em;width:auto;">
        <input type="checkbox" id="filter-selected" style="width:auto;display:inline-block;vertical-align:middle;" />
        Show only selected
      </label>
      <label for="toggle-print-layout" style="margin-top:1.2em;display:flex;align-items:center;gap:0.5em;width:auto;">
        <input type="checkbox" id="toggle-print-layout" style="width:auto;display:inline-block;vertical-align:middle;" />
        Print layout mode
      </label>
    </div>
    <div class="main-content">
      <div class="container">
        {{content}}
      </div>
    </div>
  </body>
</html>
'''

def to_path(tiedosto):
    return tiedosto[5:]


def printtaa_html(tiedosto, sudokut):

    rows = []
    for idx, sudoku in enumerate(sudokut):
        left_title = f"{sudoku.nimi}"
        right_title = f"Ratkaistuja numeroita: {sudoku.ratkaisun_kierrokset - 1}"
        left_grid = viivoita_ruudukko(sudoku.ruudukko)
        right_grid = viivoita_ruudukko(sudoku.ratkaisu)
        png_path = to_path(sudoku.tiedosto)
        row_html = f'''
        <div class="sudoku-row" data-nimi="{sudoku.nimi}" data-valmis="{sudoku.valmis}" data-ratkaisun_kierrokset="{sudoku.ratkaisun_kierrokset}">
          <input type="checkbox" class="sudoku-select" id="sudoku-select-{idx}" />
          <div class="sudoku-col first-col">
            <div class="sudoku-title">{left_title}</div>
            <pre class="sudoku-pre">{left_grid}</pre>
            <div class="sudoku-img-wrapper">
              <img src="{png_path}" class="sudoku-img" alt="Sudoku image" />
            </div>
          </div>
          <div class="sudoku-col second-col">
            <div class="sudoku-title">{right_title}</div>
            <pre class="sudoku-pre">{right_grid}</pre>
          </div>
        </div>
        '''
        rows.append(row_html)

    html = HTML_TEMPLATE.replace("{{CSS}}", CSS).replace("{{content}}", "\n".join(rows))
    with open(tiedosto, "w", encoding="utf-8") as f:
        f.write(html)


def lue_sudokut():
    with open(json_tiedosto, "r", encoding="utf-8") as f:
        data = json.load(f)
    sudokut = [Sudoku.from_json(s) for s in data["sudokut"]]
    return sudokut

if __name__ == "__main__":
    
    sudokut = lue_sudokut()

    printtaa_html(html_tiedosto, sudokut)
