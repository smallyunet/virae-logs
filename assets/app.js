const input = document.querySelector('[data-search]');
const cards = [...document.querySelectorAll('[data-report]')];
const empty = document.querySelector('[data-empty]');
const monthViews = [...document.querySelectorAll('[data-calendar-month]')];
const calendarTitle = document.querySelector('[data-calendar-title]');
const previousMonth = document.querySelector('[data-calendar-prev]');
const nextMonth = document.querySelector('[data-calendar-next]');
let visibleMonthIndex = 0;

function showMonth(index) {
  if (!monthViews.length) return;
  visibleMonthIndex = Math.max(0, Math.min(index, monthViews.length - 1));
  monthViews.forEach((month, monthIndex) => {
    month.hidden = monthIndex !== visibleMonthIndex;
  });
  const current = monthViews[visibleMonthIndex];
  calendarTitle.textContent = current.dataset.calendarLabel;
  previousMonth.disabled = visibleMonthIndex === monthViews.length - 1;
  nextMonth.disabled = visibleMonthIndex === 0;
}

function activateDate(day, updateMonth = true) {
  cards.forEach((card) => card.classList.toggle('is-current', card.dataset.date === day));
  document.querySelectorAll('[data-calendar-date]').forEach((link) => {
    const active = link.dataset.calendarDate === day;
    link.classList.toggle('is-active', active);
    if (active) link.setAttribute('aria-current', 'date');
    else link.removeAttribute('aria-current');
  });

  if (updateMonth) {
    const monthIndex = monthViews.findIndex((month) => month.dataset.calendarMonth === day.slice(0, 7));
    if (monthIndex >= 0) showMonth(monthIndex);
  }
}

if (monthViews.length) {
  previousMonth.addEventListener('click', () => showMonth(visibleMonthIndex + 1));
  nextMonth.addEventListener('click', () => showMonth(visibleMonthIndex - 1));
  showMonth(0);
}

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

document.querySelectorAll('[data-calendar-date]').forEach((link) => {
  link.addEventListener('click', () => activateDate(link.dataset.calendarDate, false));
});

if ('IntersectionObserver' in window && cards.length) {
  const observer = new IntersectionObserver((entries) => {
    const visibleCards = entries
      .filter((entry) => entry.isIntersecting && !entry.target.hidden)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
    if (visibleCards[0]) activateDate(visibleCards[0].target.dataset.date);
  }, { rootMargin: '-15% 0px -58% 0px', threshold: [0.05, 0.25, 0.5] });
  cards.forEach((card) => observer.observe(card));
}

const initialDate = window.location.hash.match(/^#log-(\d{4}-\d{2}-\d{2})$/)?.[1] || cards[0]?.dataset.date;
if (initialDate) activateDate(initialDate);
