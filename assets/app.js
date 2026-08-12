const input = document.querySelector('[data-search]');
const cards = [...document.querySelectorAll('[data-report]')];
const empty = document.querySelector('[data-empty]');

if (input) {
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const match = !query || card.textContent.toLocaleLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    }
    if (empty) empty.hidden = visible !== 0;
  });
}

