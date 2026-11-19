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
  if (open) nav?.querySelector('a')?.focus();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && nav?.classList.contains('is-open')) closeMenu(true);
});
document.addEventListener('click', event => {
  if (!event.target.closest('.header')) closeMenu();
});
document.addEventListener('focusin', event => {
  if (nav?.classList.contains('is-open') && !event.target.closest('.header')) closeMenu();
});
nav?.addEventListener('click', event => {
  if (event.target.closest('a')) closeMenu();
});
matchMedia('(min-width: 801px)').addEventListener('change', () => closeMenu());
const consentKey = 'ego-map-consent-v2';
const lifetime = 180 * 24 * 60 * 60 * 1000;
const dialog = document.querySelector('#cookie-preferences');
const check = document.querySelector('#map-consent');
let record = null;
let memoryOnly = false;
let expiryTimer;
let preferenceOpener;
let preferenceMap;
function validRecord(value) {
  const now = Date.now();
  return value && typeof value.allowed === 'boolean' && Number.isFinite(value.at) &&
    value.at > 0 && value.at <= now && now - value.at < lifetime;
}
function refreshConsent() {
  const previous = record?.allowed === true;
  if (!memoryOnly) {
    try {
      const raw = localStorage.getItem(consentKey);
      try { record = JSON.parse(raw); } catch { record = null; }
      if (raw !== null && !validRecord(record)) localStorage.removeItem(consentKey);
    } catch { /* Keep the choice for this page when storage is unavailable. */ }
  }
  if (!validRecord(record)) record = null;
  const allowed = record?.allowed === true;
  if (dialog?.open && check && allowed !== previous) check.checked = allowed;
  clearTimeout(expiryTimer);
  if (record) {
    // Recheck after browser suspensions as well as normal timer expiry.
    const remaining = Math.max(1, record.at + lifetime - Date.now());
    expiryTimer = setTimeout(refreshConsent, Math.min(remaining, 2147483647));
  }
  syncMaps();
}
function setSaved(allowed) {
  record = {allowed: Boolean(allowed), at: Date.now()};
  try {
    localStorage.setItem(consentKey, JSON.stringify(record));
    memoryOnly = false;
  } catch {
    memoryOnly = true;
    if (!allowed) {
      try { localStorage.removeItem(consentKey); } catch { /* Storage is unavailable. */ }
    }
  }
  refreshConsent();
}
function openPreferences(event) {
  if (!dialog || !check || dialog.open) return;
  preferenceOpener = event.currentTarget;
  preferenceMap = preferenceOpener.closest('.map-box');
  refreshConsent();
  check.checked = record?.allowed === true;
  dialog.showModal();
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
  control.type = 'button';
  control.className = 'map-revoke';
  control.textContent = 'Настройки на картата';
  control.addEventListener('click', openPreferences);
  box.appendChild(control);
}
function syncMaps() {
  document.querySelectorAll('.map-box').forEach(box => {
    if (record?.allowed === true) {
      const focusLoader = box.querySelector('[data-load-map]') === document.activeElement;
      loadMap(box);
      if (focusLoader && !dialog?.open) box.querySelector('.map-revoke')?.focus({preventScroll: true});
    }
    else {
      const controls = [...box.querySelectorAll('iframe,.map-revoke')];
      const hadFocus = controls.includes(document.activeElement);
      controls.forEach(node => node.remove());
      box.querySelector('.map-content').hidden = false;
      if (hadFocus && !dialog?.open) box.querySelector('[data-load-map]')?.focus({preventScroll: true});
    }
  });
}
document.querySelectorAll('[data-preferences]').forEach(button => button.addEventListener('click', openPreferences));
document.querySelectorAll('[data-load-map]').forEach(button => button.addEventListener('click', () => setSaved(true)));
document.querySelector('[data-save-consent]')?.addEventListener('click', () => {
  setSaved(check.checked);
  dialog.close();
});
document.querySelector('[data-reject-consent]')?.addEventListener('click', () => {
  setSaved(false);
  check.checked = false;
  dialog.close();
});
document.querySelector('[data-close-preferences]')?.addEventListener('click', () => dialog.close());
dialog?.addEventListener('close', () => {
  const target = preferenceOpener?.isConnected && !preferenceOpener.closest('[hidden]') ?
    preferenceOpener : preferenceMap?.querySelector(record?.allowed ? '.map-revoke' : '[data-load-map]');
  target?.focus({preventScroll: true});
  preferenceOpener = preferenceMap = null;
});
window.addEventListener('storage', event => {
  if (event.key === consentKey || event.key === null) refreshConsent();
});
window.addEventListener('pageshow', event => { if (event.persisted) refreshConsent(); });
document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshConsent(); });
refreshConsent();
