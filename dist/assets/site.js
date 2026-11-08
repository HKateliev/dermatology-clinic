'use strict';
document.documentElement.classList.add('js-enabled');
const menu = document.querySelector('.menu-toggle');
const nav = document.querySelector('#main-nav');
function closeMenu(returnFocus = false) {
  nav?.classList.remove('is-open');
  menu?.setAttribute('aria-expanded', 'false');
  menu?.setAttribute('aria-label', 'Отвори менюто');
  if (returnFocus) menu?.focus();
}
menu?.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Затвори менюто' : 'Отвори менюто');
  nav?.classList.toggle('is-open', open);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && nav?.classList.contains('is-open')) closeMenu(true);
});
document.addEventListener('click', event => {
  if (!event.target.closest('.header')) closeMenu();
});
nav?.addEventListener('click', event => {
  if (event.target.closest('a')) closeMenu();
});
matchMedia('(min-width: 801px)').addEventListener('change', () => closeMenu());
const consentKey = 'ego-map-consent-v2';
const lifetime = 180 * 24 * 60 * 60 * 1000;
const dialog = document.querySelector('#cookie-preferences');
const check = document.querySelector('#map-consent');
let sessionConsent = false;
try {
  const record = JSON.parse(localStorage.getItem(consentKey));
  sessionConsent = record?.allowed === true && typeof record.at === 'number' &&
    record.at <= Date.now() && Date.now() - record.at < lifetime;
} catch { /* Consent works in memory when browser storage is unavailable. */ }
function setSaved(allowed) {
  sessionConsent = Boolean(allowed);
  try { localStorage.setItem(consentKey, JSON.stringify({allowed: sessionConsent, at: Date.now()})); }
  catch { /* No persistence is needed to use the map during this visit. */ }
}
function openPreferences() {
  if (!dialog || !check) return;
  check.checked = sessionConsent;
  if (!dialog.open) dialog.showModal();
}
function loadMap(box) {
  if (box.querySelector('iframe')) return;
  const frame = document.createElement('iframe');
  frame.title = 'Карта: EGO, ул. Селиолу 11, Варна';
  frame.src = 'https://www.google.com/maps?q=' + encodeURIComponent('EGO Селиолу 11 Варна') + '&output=embed';
  frame.loading = 'lazy';
  frame.referrerPolicy = 'no-referrer';
  box.querySelector('.map-content').hidden = true;
  box.appendChild(frame);
  const control = document.createElement('button');
  control.className = 'map-revoke';
  control.textContent = 'Настройки на картата';
  control.addEventListener('click', openPreferences);
  box.appendChild(control);
}
function syncMaps() {
  document.querySelectorAll('.map-box').forEach(box => {
    if (sessionConsent) loadMap(box);
    else {
      box.querySelectorAll('iframe,.map-revoke').forEach(node => node.remove());
      box.querySelector('.map-content').hidden = false;
    }
  });
}
document.querySelectorAll('[data-preferences]').forEach(button => button.addEventListener('click', openPreferences));
document.querySelectorAll('[data-load-map]').forEach(button => button.addEventListener('click', () => {
  setSaved(true);
  syncMaps();
  button.closest('.map-box').querySelector('.map-revoke')?.focus();
}));
document.querySelector('[data-save-consent]')?.addEventListener('click', () => {
  setSaved(check.checked);
  syncMaps();
  dialog.close();
});
document.querySelector('[data-reject-consent]')?.addEventListener('click', () => {
  setSaved(false);
  check.checked = false;
  syncMaps();
  dialog.close();
});
document.querySelector('[data-close-preferences]')?.addEventListener('click', () => dialog.close());
window.addEventListener('storage', event => {
  if (event.key === consentKey || event.key === null) {
    try {
      if (event.newValue === null || !JSON.parse(event.newValue || '{}').allowed) {
        sessionConsent = false;
        syncMaps();
      }
    } catch { sessionConsent = false; syncMaps(); }
  }
});
syncMaps();
