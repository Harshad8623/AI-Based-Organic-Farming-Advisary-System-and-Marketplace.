/* Small navigation controls and connection feedback; no remote dependency. */
(() => {
  'use strict';
  function ready() {
    document.body.dataset.enhanced = 'true';
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navigation = document.getElementById('main-navigation');
    const moreLinks = document.querySelectorAll('[data-open-navigation]');
    function setNavigation(open) {
      if (!navigation) return;
      navigation.classList.toggle('is-open', open);
      toggle?.setAttribute('aria-expanded', String(open));
      moreLinks.forEach(link => link.setAttribute('aria-expanded', String(open)));
    }
    toggle?.addEventListener('click', () => setNavigation(toggle.getAttribute('aria-expanded') !== 'true'));
    moreLinks.forEach(link => link.addEventListener('click', event => {
      event.preventDefault();
      setNavigation(true);
      window.scrollTo({top:0, behavior:'instant'});
      navigation?.querySelector('a, summary')?.focus({preventScroll:true});
    }));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        const wasOpen = navigation?.classList.contains('is-open');
        setNavigation(false);
        document.querySelectorAll('.tools-menu[open]').forEach(menu => menu.removeAttribute('open'));
        if (wasOpen && toggle && getComputedStyle(toggle).display !== 'none') toggle.focus();
      }
    });
    document.addEventListener('click', event => {
      document.querySelectorAll('.tools-menu[open]').forEach(menu => {
        if (!menu.contains(event.target)) menu.removeAttribute('open');
      });
      if (!window.bootstrap && event.target.closest('[data-bs-dismiss="alert"]')) event.target.closest('.alert')?.remove();
    });
    const notice = document.getElementById('connection-notice');
    const updateConnection = () => { if (notice) notice.hidden = navigator.onLine !== false; };
    window.addEventListener('online', updateConnection);
    window.addEventListener('offline', updateConnection);
    updateConnection();
    function localizeCalendarDates() {
      const lang = typeof I18n === 'undefined' ? 'en' : I18n.getLang();
      const formatter = new Intl.DateTimeFormat({en:'en-IN', hi:'hi-IN', mr:'mr-IN'}[lang] || 'en-IN', {day:'numeric', month:'short', year:'numeric'});
      document.querySelectorAll('time[datetime]').forEach(element => {
        const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(element.getAttribute('datetime') || '');
        if (!match) return;
        const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
        const localDay = new Date(year, month - 1, day, 12);
        if (localDay.getFullYear() !== year || localDay.getMonth() !== month - 1 || localDay.getDate() !== day) return;
        element.textContent = formatter.format(localDay);
      });
    }
    localizeCalendarDates();
    if (typeof I18n !== 'undefined') I18n.onLangChange(localizeCalendarDates);

  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
