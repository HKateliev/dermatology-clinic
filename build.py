from pathlib import Path
import html,json,shutil,re,hashlib,subprocess,sys
from urllib.parse import quote,urlsplit
from content import *
from site_pages import PATIENT_GUIDES,LEGAL_PAGES
from site_config import OUT, ORIGIN, MODE, indexable
ROOT=Path(__file__).parent
OUT.mkdir(parents=True,exist_ok=True)
if OUT != ROOT/'dist':
 shutil.copytree(ROOT/'dist/assets',OUT/'assets',dirs_exist_ok=True)
# Remove obsolete generated pages; preserve authored assets in dist/assets.
for stale in OUT.rglob('*.html'):
 stale.unlink()
BOOK=PROFILE
H=html.escape
SERV={s[0]:s for s in SERVICES};CATS={s[0]:s for s in CATEGORIES}
PAGES=[]
REVIEW_HASHES={}
INLINE_STYLES={}
def asset(name):
 file=OUT/'assets'/name
 return '/assets/'+name+'?v='+hashlib.sha256(file.read_bytes()).hexdigest()[:12]
def clean_styles(doc):
 def convert(match):
  style=match.group(1);key='s-'+hashlib.sha256(style.encode()).hexdigest()[:12]
  INLINE_STYLES[key]=style
  return f' data-style="{key}"'
 return re.sub(r' style="([^"]*)"',convert,doc)
icons={
'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
'phone':'<path d="M5 3h4l2 5-3 2c1 3 3 5 6 6l2-3 5 2v4c0 2-3 3-6 2C8 19 3 14 3 7c0-2 0-4 2-4Z"/>',
'pin':'<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/>',
'cross':'<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6Z"/>',
'check':'<path d="m5 12 4 4L19 6"/><circle cx="12" cy="12" r="10"/>',
'calendar':'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6m10-6v6M3 11h18m-14 4h4m3 0h3"/>',
'menu':'<path d="M3 6h18M3 12h18M3 18h18"/>',
'leaf':'<path d="M20 3C8 2 2 8 5 15s16 5 15-12Z"/><path d="M3 21 15 9"/>',
'people':'<circle cx="9" cy="7" r="3"/><path d="M3 21v-4a6 6 0 0 1 12 0v4m2-17a3 3 0 0 1 0 6m2 11v-4a6 6 0 0 0-3-5"/>'}
def icon(n):return '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'+icons[n]+'</svg>'
def button(label='Запази час',href=BOOK,style='',ico='arrow'):
 ext=' target="_blank" rel="noopener noreferrer"' if href.startswith('https:') else ''
 return f'<a class="btn {style}" href="{H(href)}"{ext}>{label}{icon(ico) if ico else ""}</a>'
def link(label,href):return f'<a class="text-link" href="{H(href)}">{label}{icon("arrow")}</a>'
def url(slug):return '/uslugi/'+slug+'/'
def logo():return f'<a class="logo" href="/" aria-label="EGO — начална страница"><span class="logo-art"><img src="{asset("ego-logo-original.png")}" alt="EGO" width="514" height="318"></span><span class="logo-name">ДЕРМАТОЛОГИЯ<br>Д-Р ГАЛИНА МОНЕВА</span></a>'
def portrait(cls=''):
 return f'<img class="{cls}" src="{asset("doctor.webp")}" srcset="{asset("doctor-480.webp")} 480w, {asset("doctor.webp")} 728w" sizes="(max-width: 800px) calc(100vw - 40px), 520px" alt="Д-р Галина Монева в своя кабинет" width="728" height="936" decoding="async" '+('loading="lazy"' if cls else 'fetchpriority="high"')+'>'
def actions():return '<div class="actions">'+button()+button('Обади се','tel:+359887246009','light','phone')+'</div>'
def mapbox():return f'<div class="map-box"><div class="map-content">{icon("pin")}<h3>Ще Ви очакваме във Варна.</h3><p>ул. „Селиолу“ 11<br>EGO · д-р Галина Монева</p>{button("Упътвания", "https://www.google.com/maps/search/?api=1&query="+quote("EGO ул. Селиолу 11 Варна"),"light") }<button class="map-loader js-only" data-load-map>Приеми Google Maps и зареди картата</button><p style="font-size:12px;margin-bottom:0">Картата е външна услуга. Зарежда се само след Вашия избор.</p></div><a class="map-directions" href="https://www.google.com/maps/search/?api=1&query=EGO%20Селиолу%2011%20Варна" target="_blank" rel="noopener noreferrer">Отвори в Google Maps</a></div>'
def contact():return f'<div class="contact-grid"><div><div class="eyebrow">КАБИНЕТЪТ ВЪВ ВАРНА</div><h2>Лесно ще ни намерите.</h2><div class="contact-line"><small>Адрес</small><a href="https://www.google.com/maps/search/?api=1&query={quote("EGO ул. Селиолу 11 Варна")}" target="_blank" rel="noopener noreferrer">гр. Варна, ул. „Селиолу“ 11 {icon("arrow")}</a></div><div class="contact-line"><small>Телефони</small><a href="tel:+359887246009">0887 246 009</a> &nbsp; / &nbsp; <a href="tel:+35952804949">052 80 49 49</a></div><div class="contact-line"><small>Имейл</small><a href="mailto:office@ego-estetic.com">office@ego-estetic.com</a></div><div class="contact-line"><small>Посещения с предварително записване</small><p style="font-size:14px">Понеделник: 09:00–16:00 ч.<br>За останалите дни проверете свободните часове в Superdoc или се обадете.</p></div>{button()}</div>{mapbox()}</div>'
def finalcta():return '<div class="wrap"><section class="final-cta"><div><h2>Нека започнем с преглед.</h2><p>Изберете удобен час за консултация с д-р Монева.</p></div>'+button(style='white')+'</section></div>'
def faq(items):return '<div class="faq-list">'+''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in items)+'</div>'
HOME_FAQ=[('Как да запазя час?','Изберете „Запази час“, за да отворите профила на д-р Галина Монева в Superdoc. Можете да се свържете с кабинета и на 0887 246 009.'),('Какво да нося на първия преглед?','Носете предходни медицински документи и изследвания, ако разполагате с такива, както и информация за лекарствата и продуктите, които използвате.'),('Приемат ли се деца?','Да. В професионалния профил на д-р Монева е посочено, че работи с деца. Уточнете възрастта и причината за посещението при записване.'),('Може ли процедурата да се направи при първото посещение?','Това зависи от медицинската оценка, необходимата подготовка и времето за съответната процедура. Уточнете желанието си при записване; извършването ѝ в същия ден не е гарантирано.')]
def header(active):
 nav=[('/','Начало'),('/uslugi/','Услуги'),('/za-d-r-moneva/','За д-р Монева'),('/ceni/','Цени'),('/polezno/','Полезно'),('/kontakti/','Контакти')]
 return '<a class="skip" href="#main">Към съдържанието</a><header class="header"><div class="wrap header-inner">'+logo()+'<nav class="nav" id="main-nav" aria-label="Основна навигация">'+''.join(f'<a href="{p}"'+(' aria-current="page"' if active==p else '')+f'>{n}</a>' for p,n in nav)+'</nav>'+button(style='header-book',ico='')+'<button class="menu-toggle" aria-label="Отвори менюто" aria-controls="main-nav" aria-expanded="false">'+icon('menu')+'</button></div></header><noscript><nav class="no-js-nav" aria-label="Навигация без JavaScript"><a href="/uslugi/">Услуги</a><a href="/ceni/">Цени</a><a href="/kontakti/">Контакти</a></nav></noscript>'
def footer():return f'''<footer class="footer"><div class="wrap"><div class="footer-grid"><div>{logo()}<p>EGO – Център за лазерна естетика и дерматология<br>д-р Галина Монева<br>гр. Варна, ул. „Селиолу“ 11</p></div><div><h3>За Вашето посещение</h3><div class="footer-links"><a href="/uslugi/">Услуги</a><a href="/ceni/">Цени</a><a href="/za-d-r-moneva/">За д-р Монева</a><a href="/kontakti/">Контакти и упътвания</a><a href="{BOOK}" target="_blank" rel="noopener noreferrer">Запази час в Superdoc ↗</a></div></div><div><h3>Свържете се с кабинета</h3><div class="footer-links"><a href="tel:+359887246009">0887 246 009</a><a href="tel:+35952804949">052 80 49 49</a><a href="mailto:office@ego-estetic.com">office@ego-estetic.com</a><p>С предварително записване.<br>Понеделник: 09:00–16:00 ч.<br>За останалите дни: Superdoc или по телефона.</p></div></div></div><div class="footer-bottom"><span>© 2026 EGO · д-р Галина Монева</span><div><a href="/poveritelnost/">Поверителност</a><a href="/biskvitki/">Бисквитки</a><a href="/uslovia/">Информация за сайта</a><button class="link-button" data-preferences>Настройки на бисквитките</button></div></div></div></footer><div class="mobile-actions">{button()}{button('Обади се','tel:+359887246009','light','phone')}</div><dialog class="preferences" id="cookie-preferences" aria-labelledby="preferences-title"><button class="dialog-close" data-close-preferences aria-label="Затвори настройките">×</button><h2 id="preferences-title">Вашият избор</h2><p>Сайтът не използва рекламни или аналитични бисквитки. Запазваме само избора Ви за външната карта в този браузър.</p><label><input type="checkbox" id="map-consent">Разреши вградената карта на Google Maps</label><p>При зареждане Google получава технически данни за връзката и може да използва собствени бисквитки. <a href="/biskvitki/">Повече информация</a></p><div class="actions"><button class="btn light" data-reject-consent>Само необходимите</button><button class="btn" data-save-consent>Запази избора</button></div></dialog>'''
def schema(path,title):
 clinic={'@type':'MedicalClinic','@id':ORIGIN+'/#clinic','name':'EGO – Център за лазерна естетика и дерматология','url':ORIGIN+'/','telephone':['+359887246009','+35952804949'],'email':'office@ego-estetic.com','medicalSpecialty':'https://schema.org/Dermatology','address':{'@type':'PostalAddress','streetAddress':'ул. „Селиолу“ 11','addressLocality':'Варна','addressCountry':'BG'},'sameAs':[OFFICIAL,PROFILE]}
 person={'@type':'Person','@id':ORIGIN+'/#doctor','name':'д-р Галина Монева','jobTitle':'Специалист по дерматология и венерология','url':ORIGIN+'/za-d-r-moneva/','worksFor':{'@id':ORIGIN+'/#clinic'},'sameAs':[PROFILE]}
 clinic['image']=ORIGIN+'/assets/doctor.webp'
 person['image']=ORIGIN+'/assets/doctor.webp'
 if MODE=='production':clinic['sameAs']=[PROFILE]
 g=[clinic,person,{'@type':'WebSite','@id':ORIGIN+'/#website','url':ORIGIN+'/','name':'EGO · д-р Галина Монева','inLanguage':'bg'}]
 if path!='/':
  trail=[('Начало','/')]
  if path.startswith('/uslugi/') and path!='/uslugi/':trail.append(('Услуги','/uslugi/'))
  if path.startswith('/polezno/') and path!='/polezno/':trail.append(('Полезно','/polezno/'))
  trail.append((title,path))
  g.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i,'name':n,'item':ORIGIN+p} for i,(n,p) in enumerate(trail,1)]})
 return json.dumps({'@context':'https://schema.org','@graph':g},ensure_ascii=False)
def page(path,title,desc,body,active='',draft=False):
 if any(p==path for p,_,_ in PAGES):raise ValueError('Duplicate generated URL: '+path)
 PAGES.append((path,title,draft));f=OUT/('index.html' if path=='/' else path.strip('/')+'/index.html');f.parent.mkdir(parents=True,exist_ok=True)
 seo=title.replace(' във Варна','')+' – Варна | EGO' if path!='/' else 'Дерматолог Варна – д-р Галина Монева | EGO'
 if len(desc)>170:
  first=desc.split('. ')[0].rstrip('.')+'.'
  desc=first if len(first)<=170 else title.replace(' във Варна','')+' във Варна при д-р Галина Монева. Информация за прегледа, подготовката, цените и записването на час в EGO.'
 # The private review deployment has its own canonical origin. Use the original domain only at migration.
 favicon='/favicon.svg'
 doc=f'''<!doctype html><html lang="bg"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#d92419"><title>{H(seo)}</title><meta name="description" content="{H(desc)}"><meta name="robots" content="{'noindex,follow' if draft else 'index,follow'}"><link rel="canonical" href="{ORIGIN+path}"><meta property="og:locale" content="bg_BG"><meta property="og:type" content="website"><meta property="og:site_name" content="EGO · д-р Галина Монева"><meta property="og:title" content="{H(seo)}"><meta property="og:description" content="{H(desc)}"><meta property="og:url" content="{ORIGIN+path}"><meta property="og:image" content="{ORIGIN}/assets/doctor.jpg"><meta property="og:image:width" content="728"><meta property="og:image:height" content="936"><meta property="og:image:alt" content="EGO — д-р Галина Монева, дерматология и естетична медицина, Варна"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{H(seo)}"><meta name="twitter:description" content="{H(desc)}"><meta name="twitter:image" content="{ORIGIN}/assets/doctor.jpg"><link rel="icon" href="{favicon}"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{schema(path,title)}</script><script src="/assets/site.js" defer></script></head><body>{header(active)}<main id="main">{body}</main>{footer()}</body></html>'''
 review_body=re.sub(r'<h2[^>]*>Източници</h2><ul class="source-list">.*?</ul>','',body,flags=re.S)
 REVIEW_HASHES[path]=hashlib.sha256(review_body.encode()).hexdigest()
 doc=doc.replace('<meta name="robots" content="'+('noindex,follow' if draft else 'index,follow')+'">','<meta name="robots" content="'+('index,follow' if indexable(path,draft,REVIEW_HASHES[path]) else 'noindex,follow')+'">')
 doc=doc.replace('<meta name="theme-color"', '<meta name="referrer" content="no-referrer"><meta name="theme-color"',1)
 doc=doc.replace('href="/assets/style.css"',f'href="{asset("style.css")}"')
 doc=doc.replace('src="/assets/site.js"',f'src="{asset("site.js")}"')
 doc=doc.replace('<main id="main">','<main id="main" tabindex="-1">')
 doc=doc.replace('/assets/doctor.jpg',asset('social-card.png')).replace('content="728"','content="1200"').replace('content="936"','content="630"')
 for name in ['clinic-room','treatment-room']:
  doc=doc.replace('/assets/'+name+'.jpg',asset(name+'.webp'))
 doc=doc.replace('<br>','<br> ')
 doc=clean_styles(doc)
 doc=doc.replace('</head>','<link rel="stylesheet" href="/assets/page-styles.css"></head>')
 f.write_text(doc)
def crumb(title,parent=None):return '<div class="wrap breadcrumbs"><a href="/">Начало</a><span>/</span>'+ (f'<a href="{parent[0]}">{parent[1]}</a><span>/</span>' if parent else '')+f'<span>{title}</span></div>'
def intro(title,text,eyebrow='EGO · ВАРНА'):return f'<div class="wrap"><div class="page-intro"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{text}</p></div></div>'
def sidebar():return '<aside class="sidebar"><h3>Час за Вашата кожа.</h3><p>Консултация с д-р Галина Монева в кабинета на ул. „Селиолу“ 11, Варна.</p>'+button()+button('Обади се','tel:+359887246009','light','phone')+'<p class="small"><a href="/ceni/">Виж цените →</a><br>Записването онлайн е през Superdoc.</p></aside>'
def servicecards():
 descriptions=['Преглед и диагностика на кожата, косата и ноктите.','Оценка и отстраняване на кожни образувания.','Процедури при белези, зачервяване и капиляри.','Филъри, ботулинов токсин и грижа за текстурата на кожата.','Лице и тяло, при жени и мъже.']
 photos={0:('clinic-room.jpg','Д-р Монева в кабинета на EGO'),2:('treatment-room.jpg','Процедурната зона в EGO')}
 cards=[]
 for i,(slug,name,desc,_,_) in enumerate(CATEGORIES):
  photo=''
  if i in photos:
   src,alt=photos[i];photo=f'<img class="service-photo" src="/assets/{src}" alt="{alt}" width="1200" height="{769 if src=='clinic-room.jpg' else 800}" loading="lazy">'
  cards.append(f'<a class="service-card service-{i+1}" href="{url(slug)}">{photo}<div class="service-card-body"><span class="card-no">0{i+1}</span><h3>{name}</h3><p>{descriptions[i]}</p><span class="text-link">Научи повече {icon("arrow")}</span></div></a>')
 return '<div class="services-grid">'+''.join(cards)+'</div>'
def sources(urls):
 # After migration the historical pages redirect back to this very content.
 # Keep their provenance in the audit instead of self-referencing source links.
 urls=[(u,n) for u,n in urls if MODE!='production' or urlsplit(u).hostname!=urlsplit(ORIGIN).hostname]
 if not urls:return ''
 return '<h2 style="font-size:22px">Източници</h2><ul class="source-list">'+''.join(f'<li><a href="{H(u)}" target="_blank" rel="noopener noreferrer">{H(n)}</a></li>' for u,n in urls)+'</ul>'
# Homepage
concerns=[('Акне','akne'),('Белези от акне','belezi-ot-akne'),('Бенки и кожни образувания','benki'),('Брадавици и кокоши трън','bradavici-kokoshi-tran'),('Пигментации','pigmentacii'),('Зачервяване и капиляри','rozacea-kapilyari'),('Косопад','dermatologia-venerologia'),('Кожни заболявания','dermatologichen-pregled'),('Венерологични проблеми','dermatologia-venerologia'),('Признаци на стареене','estetichna-medicina'),('Нежелано окосмяване','lazerna-epilacia')]
home=f'''<section class="hero-surface"><div class="wrap hero"><div class="hero-copy"><div class="eyebrow">Д-Р ГАЛИНА МОНЕВА · ВАРНА</div><h1>Дерматология и<br>естетична медицина.<br><em>С внимание към Вас.</em></h1><p class="intro">Специалист по дерматология и венерология с над 30 години медицински опит.</p>{actions()}<a class="location" href="/kontakti/">{icon('pin')} ул. „Селиолу“ 11, Варна</a></div><div class="hero-visual"><div class="portrait-frame">{portrait()}</div><div class="doctor-caption"><div><strong>д-р Галина Монева</strong><span>Дерматология и венерология</span></div><span class="caption-symbol" aria-hidden="true">✳</span></div></div></div></section><div class="trust-surface"><div class="wrap trust"><div>{icon('cross')}<span>30+ години медицински опит</span></div><div>{icon('people')}<span>Прегледи за възрастни и деца</span></div><div>{icon('check')}<span>Лазерна дерматохирургия</span></div></div></div><section class="wrap concern-section"><div class="section-head"><h2>Какво Ви притеснява?</h2><a class="text-link" href="/uslugi/">Всички услуги {icon('arrow')}</a></div><div class="concerns">{''.join(f'<a class="concern" href="{url(slug)}"><span>{name}</span>{icon("arrow")}</a>' for name,slug in concerns)}</div></section><section class="section services-section"><div class="wrap"><div class="section-head"><div><div class="eyebrow">УСЛУГИ В EGO</div><h2>От прегледа<br>до подходящото лечение.</h2></div><p>Методът се определя след медицинска оценка.</p></div>{servicecards()}</div></section><section class="section wrap about-home"><div class="practice-image"><img src="/assets/clinic-room.jpg" alt="Д-р Галина Монева в кабинета на EGO" width="1200" height="769" loading="lazy"><span>Снимка от професионалния профил на практиката</span></div><div class="doctor-copy"><div class="eyebrow">ЛЕКАРЯТ ЗАД EGO</div><h2>Д-р Галина Монева</h2><p>Завършва медицина във Варна през 1989 г. Придобива специалност по дерматология през 1994 г. От 2019 г. развива практиката си в EGO.</p>{link('Повече за д-р Монева','/za-d-r-moneva/')}<a class="review-inline" href="{PROFILE}" target="_blank" rel="noopener noreferrer"><span>Superdoc</span><span>Мнения на пациенти ↗</span></a></div></section><section class="visit-surface"><div class="wrap visit-layout"><h2>Първото посещение<br>в три стъпки.</h2><div class="steps">{''.join(f'<div class="step"><span class="step-no">0{i+1}</span><div><h3>{title}</h3><p>{text}</p></div></div>' for i,(title,text) in enumerate([('Запазвате час','Онлайн или по телефона.'),('Преглед и оценка','Обсъждате оплакванията и очакванията си.'),('План за лечение','С ясни указания за следващите стъпки.')]))}</div></div></section><section class="section wrap faq-grid"><div><div class="eyebrow">ПРЕДИ ПОСЕЩЕНИЕТО</div><h2>Полезно е да знаете.</h2></div>{faq(HOME_FAQ[1:])}</section><section class="contact-home"><div class="wrap"><div class="contact-grid"><div><div class="eyebrow">EGO · ВАРНА</div><h2>Очакваме Ви<br>на ул. „Селиолу“ 11.</h2><a class="contact-phone" href="tel:+359887246009">0887 246 009</a><p><a href="tel:+35952804949">052 80 49 49</a> · <a href="mailto:office@ego-estetic.com">office@ego-estetic.com</a></p><p class="contact-hours">С предварително записване.<br>Понеделник: 09:00–16:00 ч. За останалите дни проверете в Superdoc или се обадете.</p>{actions()}</div>{mapbox()}</div></div></section>'''

page('/','Дерматолог Варна','Д-р Галина Монева: дерматологични прегледи, дерматоскопия, лазерна и естетична медицина във Варна. Ул. „Селиолу“ 11. Запазете час.',home,'/')
page('/uslugi/','Услуги','Прегледи, дерматохирургия, лазерна дерматология, естетична медицина и лазерна епилация в EGO, Варна.',crumb('Услуги')+intro('Медицинска грижа за кожата.','Изберете направление или започнете с дерматологичен преглед, ако не сте сигурни от какво се нуждаете.')+'<section class="section wrap">'+servicecards()+'</section>'+finalcta(),'/uslugi/')
# Five category landing pages. Hair removal category doubles as the detailed service page.
for s,n,d,slugs,body in CATEGORIES:
 if s in SERV:continue  # One canonical hair-removal page, with the detailed template.
 links=''.join(f'<a class="article-link" href="{url(k)}"><span>{SERV[k][1]}</span>{icon("arrow")}</a>' for k in slugs)
 txt=f'<h2>Каква помощ можете да получите?</h2><p>{body}</p><div class="article-links">{links}</div><h2>Първо обсъждаме Вашия случай.</h2><p>На консултацията споделете от кога е оплакването, какво сте използвали досега и каква промяна очаквате. Носете предишни изследвания и информация за приеманите лекарства.</p><p>При процедура се уточняват подготовката, обезболяването, възстановяването и рисковете. Решението се взема след преглед, а не само по избор на услуга от сайта.</p><h2>Цени и записване</h2><p>Вижте публикуваните цени по категории. За конкретния обхват на процедурата и пакетните условия се свържете с кабинета.</p><p>{link("Виж цените","/ceni/")}</p>'
 page(url(s),n,d,crumb(n,('/uslugi/','Услуги'))+intro(n,d)+f'<div class="wrap content-grid"><div class="prose">{txt}</div>{sidebar()}</div>'+finalcta(),'/uslugi/')
# Source-based service pages: no added clinical protocols or unverified medical bylines.
for slug,name,category,description,sections,questions,source_urls in SERVICES:
 cat=CATS[category]
 body=''.join(f'<h2>{H(title)}</h2><p>{H(text)}</p>' for title,text in sections)
 body+='<h2>Цена и записване</h2><p>Вижте ценовата листа на EGO. За обхвата на процедурата и пакетните условия се свържете с кабинета.</p>'+link('Виж цените','/ceni/')
 body+='<h2>Често задавани въпроси</h2>'+faq(questions)
 body+='<p class="meta">Информацията представя публикуваните услуги и отговори на EGO. Методът се определя след преглед.</p>'
 page(url(slug),name+' във Варна',description,crumb(name,('/uslugi/','Услуги'))+intro(name,description,cat[1].upper()+' · ВАРНА')+f'<div class="wrap content-grid"><article class="prose">{body}</article>{sidebar()}</div>'+finalcta(),'/uslugi/')
# Doctor profile
bio=f'''<section class="section wrap doctor-section"><div class="doctor-portrait-panel">{portrait('doctor-photo')}<p class="portrait-note">д-р Галина Монева<br><span>Дерматология и венерология</span></p></div><div class="doctor-copy"><div class="eyebrow">СПЕЦИАЛИСТ ПО ДЕРМАТОЛОГИЯ И ВЕНЕРОЛОГИЯ</div><h1>Д-р Галина Монева</h1><p class="subtitle" style="margin-top:20px">Над 30 години медицински опит</p><p>Д-р Монева практикува клинична дерматология, лазерна дерматохирургия и естетична медицина във Варна. В EGO приема възрастни и деца.</p><p>Професионалната ѝ подготовка включва медицина, специализация по дерматология и допълнителни обучения по лазерни и инжекционни методи.</p>{actions()}</div></section><div class="wrap content-grid"><div class="prose"><h2>Образование и професионален път</h2><div class="timeline"><div><strong>1989</strong><p>Завършва медицина във Висшия медицински институт във Варна. Преди това завършва медицинска козметика в Полувисшия медицински институт в София.</p></div><div><strong>1994</strong><p>Придобива специалност по дерматология.</p></div><div><strong>1995</strong><p>След работа в МБАЛ Тутракан развива частен кабинет в периода 1995–2010 г.</p></div><div><strong>2010</strong><p>До 2018 г. работи като специалист дерматолог в лазерно студио.</p></div><div><strong>2019</strong><p>Започва самостоятелна практика в Център за лазерна естетика и дерматология EGO във Варна.</p></div></div><h2>Допълнителни квалификации</h2><p>В публичния професионален профил са посочени квалификации по лазерна дерматохирургия с CO₂, Alexandrite, Nd:YAG и Q-switched лазери, както и дермални филъри, ботулинов токсин, мезотерапии и колагенови терапии.</p><p>Допълнителните обучения са част от професионалния ѝ път. Методът за конкретната процедура се обсъжда по време на консултацията.</p><h2>Професионален профил и мнения</h2><p>Пълната публична биография и актуалните мнения на пациенти можете да видите в Superdoc.</p>{link('Профил на д-р Монева в Superdoc',PROFILE)}<p class="meta">Биографичните данни са сверени с публичния професионален профил на {DATE}.</p></div>{sidebar()}</div>'''
page('/za-d-r-moneva/','За д-р Галина Монева','Образование, специалност и професионален опит на д-р Галина Монева, дерматолог във Варна. EGO, ул. „Селиолу“ 11.',crumb('За д-р Монева')+bio+finalcta(),'/za-d-r-moneva/')
# Prices: the current official EGO website is the sole price authority.
pricebody=crumb('Цени')+intro('Цени на прегледи и процедури','Цените са в евро. За конкретната процедура и пакетните условия се свържете с кабинета.','ЦЕНОВА ЛИСТА · EUR')+'<div class="wrap"><nav class="price-nav" aria-label="Категории цени">'+''.join(f'<a href="#{slug}">{name}</a>' for slug,name,_ in PRICES)+'</nav><p class="meta">По актуалната ценова листа на EGO · сверено на '+DATE+' г.</p>'
for slug,name,rows in PRICES:
 pricebody+=f'<section class="price-group" id="{slug}"><h2>{name}</h2>'
 if rows:
  pricebody+=f'<table class="price-table"><caption>{name} — цени в евро</caption><thead><tr><th scope="col">Услуга</th><th scope="col">Цена в EUR</th></tr></thead><tbody>'+''.join(f'<tr><td>{H(label)}</td><td class="{("price-pending" if len(price)>15 else "")}">{H(price)}</td></tr>' for label,price in rows)+'</tbody></table>'
 else:
  pricebody+='<p>За цена на конкретна зона се обадете на <a class="text-link" href="tel:+359887246009">0887 246 009</a>. В публикуваната ценова листа на EGO няма отделни стойности за епилация по зони.</p>'
 pricebody+='</section>'
pricebody+='<div class="note"><p>За повече кожни образувания са посочени пакетни цени. При филърите уточнете продукта и количеството. Подготовката и обхватът на конкретната процедура се обсъждат с кабинета.</p></div></div>'+finalcta()
page('/ceni/','Цени','Цени в евро за кожен преглед, дерматоскопия, лазерни и естетични процедури в EGO, Варна. Актуална ценова листа на кабинета.',pricebody,'/ceni/')
# Contact
contactbody=crumb('Контакти')+intro('Контакти и записване','Център за лазерна естетика и дерматология · д-р Галина Монева','КОНТАКТИ')+'<section class="wrap section">'+contact()+'</section><div class="wrap prose" style="padding-bottom:70px"><h2>Преди посещението</h2><p>Запазете час предварително. Носете предходни медицински документи и изследвания. За процедурите уточнете дали е необходима подготовка.</p><p>Имейлът е за организационни въпроси. Не изпращайте подробна медицинска история или снимки на интимни области. Медицинска оценка се прави на преглед.</p><div class="note"><p>Публикуваното работно време е понеделник, 09:00–16:00 ч. За часовете през останалите дни използвайте Superdoc или се свържете с кабинета.</p></div></div>'
page('/kontakti/','Контакти','EGO, д-р Галина Монева. Варна, ул. „Селиолу“ 11. Тел. 0887 246 009 и 052 80 49 49. Записване през Superdoc и по телефона.',contactbody,'/kontakti/')
# Patient guides restate the practice's existing FAQ, not new medical articles.
articlesbody=crumb('Полезно')+intro('Полезно за пациентите','Кратки отговори по публикуваната информация на кабинета — за прегледите, дерматоскопията и лазерните процедури.','ПРЕДИ ПОСЕЩЕНИЕТО')+'<div class="wrap"><div class="article-cards">'+''.join(f'<article class="article-card"><span class="meta">ИНФОРМАЦИЯ ОТ EGO</span><h2>{H(name)}</h2><p>{H(description)}</p>{link("Научи повече","/polezno/"+slug+"/")}</article>' for slug,name,description,*_ in PATIENT_GUIDES)+'</div></div>'
page('/polezno/','Полезно за пациентите','Практична информация за прегледи на бенки, дерматоскопия, обезболяване и планиране на лазерни процедури в EGO.',articlesbody,'/polezno/')
for slug,name,description,sections,related,source_paths in PATIENT_GUIDES:
 body=f'<p class="meta">По публикуваните материали на EGO — д-р Галина Монева.<br>Редактирано: {DATE} г.</p>'
 body+=''.join(f'<h2>{H(title)}</h2><p>{H(text)}</p>' for title,text in sections)
 body+='<div class="note">Информацията не замества преглед и индивидуалните указания на лекаря.</div>'+link('Виж услугата',url(related))
 page('/polezno/'+slug+'/',name,description,crumb(name,('/polezno/','Полезно'))+intro(name,description,'ПОЛЕЗНО ЗА ПАЦИЕНТИТЕ')+f'<div class="wrap content-grid"><article class="prose">{body}</article>{sidebar()}</div>','/polezno/')
for slug,(name,text) in LEGAL_PAGES.items():
 page('/'+slug+'/',name,name+' — EGO, д-р Галина Монева, Варна.',crumb(name)+intro(name,'Информация за използването на сайта и връзката с кабинета.')+f'<div class="wrap content-grid"><article class="prose">{text}<p class="meta">Актуализирано: {DATE} г.</p></article>{sidebar()}</div>')
# Correct not-found document
notfound=intro('Тази страница не е намерена.','Възможно е адресът да е променен. Можете да разгледате услугите или да се върнете към началото.','ГРЕШКА 404')+'<div class="wrap section">'+button('Към началото','/','')+' '+button('Всички услуги','/uslugi/','light')+'</div>'
page('/404/','Страницата не е намерена','Страницата не е намерена.',notfound,draft=True)
shutil.copy(OUT/'404/index.html',OUT/'404.html')
# 301 mapping for every discovered legacy content URL. Source domain DNS migration is a separate step.
redirects={'/bg/info/privacy/':'/poveritelnost/','/bg/info/promocii/':'/ceni/','/bg/news/':'/polezno/','/bg/':'/','/bg':'/','/bg/info/ceni/':'/ceni/','/bg/contacts/':'/kontakti/',
'/bg/products/dermatologiya-i-venerologiya/':url('dermatologia-venerologia'),'/bg/products/dermatohirurgiya/':url('dermatohirurgia'),'/bg/products/estetichna-medicina/':url('estetichna-medicina'),'/bg/products/lazerna-estetika/':url('lazerna-dermatologia'),'/bg/products/lazerna-epilaciya/':url('lazerna-epilacia'),'/bg/news_more/nai-esto-zadavani-vyprosi-v-dermatohirurgiyata/':url('dermatohirurgia'),'/bg/news_more/nai-chesto-zadavani-vyprosi-v-medicinskata-estetika/':url('estetichna-medicina'),'/bg/news_more/nai-esto-zadavani-vyprosi-v-lazernata-estetika/':url('lazerna-dermatologia'),'/bg/news_more/novosti-za-lazeren-centyr-ego/':'/za-d-r-moneva/','/bg/news_more/myjka-kozmetologiya-i-lazerna-estetika/':url('estetichna-medicina')}
redirects.update({a.rstrip('/'):b for a,b in list(redirects.items()) if a.endswith('/') and a.rstrip('/') not in redirects})
(OUT/'_redirects').write_text('\n'.join(f'{a} {b} 301' for a,b in redirects.items())+'\n')
# Fixed same-origin resources and an opt-in map are the only browser dependencies.
csp="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src https://www.google.com https://maps.google.com; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
headers={'Content-Security-Policy':csp,'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'SAMEORIGIN','Permissions-Policy':'camera=(), microphone=(), geolocation=(), payment=(), usb=()','Strict-Transport-Security':'max-age=31536000'}
if MODE=='preview':headers['X-Robots-Tag']='noindex, follow'
(OUT/'_headers').write_text('/*\n'+''.join('  '+k+': '+v+'\n' for k,v in headers.items())+'/assets/*\n  Cache-Control: public, max-age=86400\n/\n  Cache-Control: public, max-age=0, must-revalidate\n/*/\n  Cache-Control: public, max-age=0, must-revalidate\n/*.html\n  Cache-Control: public, max-age=0, must-revalidate\n/robots.txt\n  Cache-Control: public, max-age=0, must-revalidate\n/sitemap.xml\n  Cache-Control: public, max-age=0, must-revalidate\n')
shutil.copy(OUT/'assets/favicon.svg',OUT/'favicon.svg')
(OUT/'assets/page-styles.css').write_text('\n'.join('[data-style="'+key+'"]{'+style+'}' for key,style in sorted(INLINE_STYLES.items())))
# Version the generated stylesheet as well as the authored assets.
for doc in OUT.rglob('*.html'):
 text=doc.read_text().replace('href="/assets/page-styles.css"', 'href="'+asset('page-styles.css')+'"')
 # Meta fallback also applies on static hosts without custom-header support.
 meta_csp=csp.replace("; frame-ancestors 'self'",'')
 text=text.replace('<meta name="viewport"', '<meta http-equiv="Content-Security-Policy" content="'+H(meta_csp)+'"><meta name="viewport"',1)
 doc.write_text(text)
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+ORIGIN+p+'</loc></url>' for p,_,draft in PAGES if indexable(p,draft,REVIEW_HASHES[p]))+'</urlset>')
(ROOT/'redirect-map.json').write_text(json.dumps(redirects,ensure_ascii=False,indent=2))
(ROOT/'page-inventory.json').write_text(json.dumps([{'url':p,'title':t,'pending_review':d,'content_sha256':REVIEW_HASHES[p],'indexable':indexable(p,d,REVIEW_HASHES[p])} for p,t,d in PAGES],ensure_ascii=False,indent=2))
(OUT/'build-info.json').write_text(json.dumps({'mode':MODE,'origin':ORIGIN,'page_count':len(PAGES)},indent=2))
print(f'Generated {len(PAGES)} unique pages in {MODE} mode; {len(redirects)} mapped legacy URLs.')

subprocess.run([sys.executable,str(ROOT/"build_worker.py"),str(OUT)],check=True)
