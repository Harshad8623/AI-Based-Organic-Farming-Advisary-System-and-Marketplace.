/* Navigation and connection feedback work without third-party JavaScript. */
(() => {
  'use strict';
  function ready() {
    document.body.dataset.enhanced = 'true';
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navigation = document.getElementById('main-navigation');
    if (toggle && navigation) {
      toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        toggle.setAttribute('aria-expanded', String(open));
        navigation.classList.toggle('is-open', open);
      });
      document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
          navigation.classList.remove('is-open');
          toggle.setAttribute('aria-expanded', 'false');
          document.querySelectorAll('.tools-menu[open]').forEach(menu => menu.removeAttribute('open'));
        }
      });
    }
    document.addEventListener('click', event => {
      document.querySelectorAll('.tools-menu[open]').forEach(menu => {
        if (!menu.contains(event.target)) menu.removeAttribute('open');
      });
      if (!window.bootstrap && event.target.closest('[data-bs-dismiss="alert"]')) {
        event.target.closest('.alert')?.remove();
      }
    });
    const notice = document.getElementById('connection-notice');
    const updateConnection = () => { if (notice) notice.hidden = navigator.onLine !== false; };
    window.addEventListener('online', updateConnection);
    window.addEventListener('offline', updateConnection);
    updateConnection();
    // Important form errors remain visible until the user dismisses them.
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
