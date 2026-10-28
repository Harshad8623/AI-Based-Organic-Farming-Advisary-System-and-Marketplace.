/* Same-origin CSRF protection for forms and JSON requests. */
(() => {
  const token = () => document.querySelector('meta[name="csrf-token"]')?.content || '';
  const unsafe = method => !['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase());
  const originalFetch = window.fetch.bind(window);
  window.fetch = (resource, options = {}) => {
    const url = new URL(resource instanceof Request ? resource.url : resource, location.href);
    const method = options.method || (resource instanceof Request ? resource.method : 'GET');
    if (url.origin === location.origin && unsafe(method)) {
      const headers = new Headers(options.headers || (resource instanceof Request ? resource.headers : {}));
      headers.set('X-CSRF-Token', token());
      options = {...options, headers};
    }
    return originalFetch(resource, options);
  };
  function protect(form) {
    if (new URL(form.action || location.href, location.href).origin !== location.origin || !unsafe(form.method || 'GET')) return;
    let field = form.querySelector('input[name="csrf_token"]');
    if (!field) {
      field = document.createElement('input');
      field.type = 'hidden'; field.name = 'csrf_token'; form.appendChild(field);
    }
    field.value = token();
  }
  document.addEventListener('DOMContentLoaded', () => document.querySelectorAll('form').forEach(protect));
  document.addEventListener('submit', event => { if (event.target instanceof HTMLFormElement) protect(event.target); }, true);
})();
