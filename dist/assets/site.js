const menu=document.querySelector('.menu-toggle'),nav=document.querySelector('#main-nav');
menu?.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Затвори менюто':'Отвори менюто');nav.classList.toggle('is-open',open)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&nav?.classList.contains('is-open')){nav.classList.remove('is-open');menu.setAttribute('aria-expanded','false');menu.focus()}});
const consentKey='ego-map-consent-v1',dialog=document.querySelector('#cookie-preferences'),check=document.querySelector('#map-consent');
function saved(){try{return localStorage.getItem(consentKey)==='yes'}catch{return false}}
function setSaved(v){try{localStorage.setItem(consentKey,v?'yes':'no')}catch{}}
function loadMap(box){if(box.querySelector('iframe'))return;box.querySelector('.map-content').hidden=true;const f=document.createElement('iframe');f.title='Карта: EGO, ул. Селиолу 11, Варна';f.src='https://maps.google.com/maps?q='+encodeURIComponent('EGO Селиолу 11 Варна')+'&output=embed';f.loading='lazy';f.referrerPolicy='no-referrer-when-downgrade';box.appendChild(f);const b=document.createElement('button');b.className='map-revoke';b.textContent='Настройки на картата';b.addEventListener('click',openPreferences);box.appendChild(b)}
function syncMaps(){document.querySelectorAll('.map-box').forEach(box=>{if(saved())loadMap(box);else{box.querySelectorAll('iframe,.map-revoke').forEach(x=>x.remove());box.querySelector('.map-content').hidden=false}})}
function openPreferences(){check.checked=saved();dialog.showModal()}
document.querySelectorAll('[data-preferences]').forEach(b=>b.addEventListener('click',openPreferences));
document.querySelectorAll('[data-load-map]').forEach(b=>b.addEventListener('click',()=>{setSaved(true);syncMaps()}));
document.querySelector('[data-save-consent]')?.addEventListener('click',()=>{setSaved(check.checked);syncMaps();dialog.close()});
document.querySelector('[data-reject-consent]')?.addEventListener('click',()=>{setSaved(false);check.checked=false;syncMaps();dialog.close()});
syncMaps();
