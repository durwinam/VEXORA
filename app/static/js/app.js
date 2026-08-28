(function () {
  'use strict';
  const root = document.documentElement;
  const key = 'vexora-theme';
  const saved = localStorage.getItem(key);
  if (saved === 'light') root.dataset.theme = 'light';
  const button = document.querySelector('[data-theme-toggle]');
  if (!button) return;
  button.addEventListener('click', function () {
    const light = root.dataset.theme === 'light';
    if (light) {
      delete root.dataset.theme;
      localStorage.setItem(key, 'dark');
    } else {
      root.dataset.theme = 'light';
      localStorage.setItem(key, 'light');
    }
  });
})();
