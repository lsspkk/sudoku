document.addEventListener('DOMContentLoaded', function() {
  // Update sudoku counter
  const counterArea = document.getElementById('sudoku-counter-area') || document.querySelector('.sudoku-count');
  const items = document.querySelectorAll('.item');
  if (counterArea) {
    counterArea.textContent = 'Sudokus: ' + items.length;
  }

  // Checkbox filter
  const checkbox = document.getElementById('hide-lowmed-checkbox') || document.getElementById('hide-high-checkbox');
  if (checkbox) {
    checkbox.addEventListener('change', function() {
      items.forEach(item => {
        if (item.classList.contains('low') || item.classList.contains('medium')) {
          if (checkbox.checked) {
            item.classList.add('hidden');
          } else {
            item.classList.remove('hidden');
          }
        }
      });
    });
  }
}); 