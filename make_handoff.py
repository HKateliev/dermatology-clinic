"""Build a clean, production-domain static handoff; no credentials or Sites identity."""
from pathlib import Path
import argparse,subprocess,json,shutil,re,hashlib,zipfile,html
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',default=str(ROOT/'delivery'))
parser.add_argument('--source-ref',default='main')
args=parser.parse_args()
DEST=Path(args.output_dir).resolve()
PUBLIC=DEST/'EGO-website-handoff'/'public_html'
DOCS=DEST/'EGO-website-handoff'/'handoff'
STAGE=ROOT/'handoff-public'
subprocess.run(['python3','build.py','--mode','production','--output','handoff-public'],cwd=ROOT,check=True)
subprocess.run(['python3','validate.py','--output','handoff-public'],cwd=ROOT,check=True)
subprocess.run(['node','worker/validate.mjs','handoff-public'],cwd=ROOT,check=True)
production_validation=json.loads((ROOT/'validation-report.json').read_text())
if production_validation['errors']:raise SystemExit('Production validation failed')
if PUBLIC.parent.exists():shutil.rmtree(PUBLIC.parent)
PUBLIC.mkdir(parents=True);DOCS.mkdir()
allowed={'.html','.css','.js','.webp','.png','.svg','.xml','.txt'}
for source in sorted(STAGE.rglob('*')):
 if not source.is_file():continue
 relative=source.relative_to(STAGE)
 if relative.parts[0]=='server':continue
 if source.suffix not in allowed and source.name not in {'_headers','_redirects'}:continue
 target=PUBLIC/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
origin='https://www.ego-estetic.com'
redirects=json.loads((ROOT/'redirect-map.json').read_text())
headers={}
for line in (STAGE/'_headers').read_text().splitlines()[1:]:
 if not line.startswith(' '):break
 key,value=line.strip().split(':',1);headers[key]=value.strip()
assert 'X-Robots-Tag' not in headers
apache=['# Apache 2.4: install at the document root with the new site.',
 '# Required: AllowOverride for FileInfo, Indexes/Options and AuthConfig; mod_rewrite, mod_headers.',
 'Options -Indexes -MultiViews','DirectoryIndex index.html','ErrorDocument 404 /404.html',
 '<IfModule mod_mime.c>','  AddType image/webp .webp','  AddType image/svg+xml .svg','  AddType text/javascript .js','</IfModule>',
 '<IfModule mod_rewrite.c>','RewriteEngine On','RewriteCond %{REQUEST_METHOD} !^(GET|HEAD)$ [NC]','RewriteRule ^ - [R=405,L]',
 r'RewriteRule (^|/)\.(?!well-known/) - [R=404,L]','RewriteRule ^_(headers|redirects)$ - [R=404,L]']
# Exact old URLs redirect straight to the canonical destination, with query retained.
seen=set()
for old,new in redirects.items():
 stripped=old.strip('/')
 if stripped in seen:continue
 seen.add(stripped)
 apache.append('RewriteRule ^'+re.escape(stripped)+'/?$ '+origin+new+' [R=301,L,NE]')
apache+=['# For a reverse proxy, use the host\'s trusted HTTPS setting; never trust arbitrary forwarded headers.',
 'RewriteCond %{HTTPS} !=on [OR]',r'RewriteCond %{HTTP_HOST} !^www\.ego-estetic\.com$ [NC]',
 'RewriteRule ^ '+origin+'%{REQUEST_URI} [R=301,L,NE]',
 'RewriteCond %{THE_REQUEST} \\s/+(.*/)?index\\.html(?:[?\\s]) [NC]',
 'RewriteRule ^(.*)index\\.html$ '+origin+'/$1 [R=301,L,NE]','</IfModule>',
 '<IfModule mod_headers.c>','  Header always set Allow "GET, HEAD"']
for key,value in headers.items():apache.append('  Header always set '+key+' "'+value.replace('"','\\"')+'"')
apache+=['  Header set Cache-Control "public, max-age=0, must-revalidate"',
 '  <FilesMatch "\\.(?:css|js|webp|png|jpg|jpeg|svg|ico)$">','    Header set Cache-Control "public, max-age=86400"','  </FilesMatch>','</IfModule>',
 '<FilesMatch "\\.(?:py|mjs|map|log|ini|env|sql|bak|zip|tar|gz)$">','  Require all denied','</FilesMatch>',
 '<IfModule mod_deflate.c>','  AddOutputFilterByType DEFLATE text/html text/css text/javascript application/xml image/svg+xml','</IfModule>']
(PUBLIC/'.htaccess').write_text('\n'.join(apache)+'\n')
# Nginx: snippets are intentionally outside public_html and require host-specific installation.
nginx_maps=['# Include in the nginx http {} context, not in a location block.',
 'map $uri $ego_legacy {','    default "";']
nginx_maps += ['    '+old+' '+new+';' for old,new in redirects.items()]
nginx_maps += ['}','map $uri $ego_cache_control {','    default "public, max-age=0, must-revalidate";','    ~^/assets/ "public, max-age=86400";','}']
(DOCS/'nginx-maps.conf').write_text('\n'.join(nginx_maps)+'\n')
nginx=['# Template: merge into the CURRENT virtual host. Set the actual root and existing TLS certificate paths.',
 '# Load nginx-maps.conf in http {} first. nginx -t must pass before reload.',
 'server {','    listen 80;','    server_name ego-estetic.com www.ego-estetic.com;',
 '    if ($ego_legacy != "") { return 301 '+origin+'$ego_legacy$is_args$args; }',
 '    return 301 '+origin+'$request_uri;','}',
 'server {','    listen 443 ssl;','    server_name ego-estetic.com www.ego-estetic.com;',
 '    root /REPLACE/WITH/ACTUAL/public_html;','    ssl_certificate /REPLACE/WITH/EXISTING/fullchain.pem;',
 '    ssl_certificate_key /REPLACE/WITH/EXISTING/privkey.pem;','    index index.html;',
 '    error_page 404 /404.html;','    autoindex off;',
 '    if ($request_method !~ ^(GET|HEAD)$) { return 405; }',
 '    if ($ego_legacy != "") { return 301 '+origin+'$ego_legacy$is_args$args; }',
 '    if ($host != www.ego-estetic.com) { return 301 '+origin+'$request_uri; }',
 '    add_header Allow "GET, HEAD" always;']
for key,value in headers.items():nginx.append('    add_header '+key+' "'+value.replace('"','\\"')+'" always;')
nginx+=['    add_header Cache-Control $ego_cache_control always;',
 '    location ~ /\\.(?!well-known/) { return 404; }',
 '    location ~ \\.(?:py|mjs|map|log|ini|env|sql|bak|zip|tar|gz)$ { return 404; }',
 '    location = /_headers { return 404; }','    location = /_redirects { return 404; }']
inventory=json.loads((ROOT/'page-inventory.json').read_text())
for entry in inventory:
 path=entry['url']
 if path!='/':nginx.append('    location = '+path.rstrip('/')+' { return 301 '+path+'$is_args$args; }')
nginx+=['    location / { try_files $uri $uri/ =404; }','}']
(DOCS/'nginx-site.conf').write_text('\n'.join(nginx)+'\n')
shutil.copyfile(ROOT/'audit_http.py',DOCS/'audit_http.py')
shutil.copyfile(ROOT/'page-inventory.json',DOCS/'page-inventory.json')
(DOCS/'redirect-map.json').write_text(json.dumps(redirects,ensure_ascii=False,indent=2))
(DOCS/'production-validation.json').write_text(json.dumps(production_validation,ensure_ascii=False,indent=2))
# The production serving bundle is an alternative for Cloudflare, not a public source file.
shutil.copyfile(STAGE/'server/index.js',DOCS/'cloudflare-worker.mjs')
(DOCS/'release-info.json').write_text(json.dumps({'production_origin':origin,'source_repository':'https://github.com/HKateliev/dermatology-clinic','source_ref':args.source_ref,'pages':34,'indexable_pages':production_validation['sitemap_urls'],'price_authority':'https://www.ego-estetic.com/bg/info/ceni/','photos_confirmed_by_user':True,'prepared_on':'2026-11-08','requires_destination_checks':True},ensure_ascii=False,indent=2))
readme='''# EGO — пакет за публикуване

Това е готов статичен сайт за https://www.ego-estetic.com. Има 34 страници, реални изображения, цени от текущия сайт и пренасочвания за намерените стари адреси. Не е тема за WordPress и не се импортира в стария административен панел. За бъдещи промени е предоставен изходният проект в GitHub.

## Какво се качва

**На хостинга се качва само съдържанието на public_html/.** Не качвайте цялата външна папка и не публикувайте handoff/, изходен код, резервни копия или самия ZIP. Не поставяйте новия сайт под /new/: връзките и ресурсите са за корена на домейна.

- Apache/LiteSpeed: файловете от public_html/, включително скрития .htaccess. Нужни са mod_rewrite, mod_headers и подходящ AllowOverride. Ако отделни директиви са забранени от доставчика, преместете еквивалентната конфигурация във virtual host; не пускайте сайта с неработещи правила. Зад reverse proxy ползвайте HTTPS настройката на доставчика, за да няма redirect loop.
- Nginx: public_html/ плюс приложените nginx-maps.conf и nginx-site.conf като пример за текущия virtual host. Заменете корена и сертификатните пътища. Проверете с nginx -t. Тези файлове не се качват в публичната директория.
- Cloudflare Worker: алтернатива е handoff/cloudflare-worker.mjs. Той съдържа публичните ресурси и налага заглавки, 301, 404, 405 и ETag. Не изисква asset binding. Не го качвайте като достъпен JS файл в public_html.

## Последователност

1. Направете пълен backup на старите файлове, базата данни (ако има такава) и конфигурацията. Запазете извън публичната директория. Запишете бърза процедура за връщане.
2. Потвърдете с кабинета точния доставчик/администратор на данни и регистрационните му данни от реалните документи. Старият privacy URL е проверен в браузър и е празен. В новия текст са използвани публикуваните име и контакти плюс реалните функции на сайта; не е измислено юридическо лице/ЕИК. Допълнете точната идентификация и конкретните хостинг/логови срокове преди официалното включване.
3. Подгответе защитен staging virtual host с корен public_html. Не го оставяйте публично индексируем. За staging временно адаптирайте canonical-host редиректа към тестовия host или тествайте с официалния Host чрез локално резолвиране; преди включване върнете правилата за www.ego-estetic.com. В handoff/ има и audit_http.py с нужните JSON файлове за проверка след инсталиране: python3 audit_http.py --origin https://www.ego-estetic.com. Проверете конфигурацията за използвания реален сървър; Apache/Nginx не са били достъпни за тест в средата на изработка.
4. Подменете web document root с новите публични файлове и правилата за сървъра. Не оставяйте стария index.php да има предимство пред index.html. Не оставяйте стари PHP/CMS, backup и конфигурационни файлове в новия публичен root.
5. Запазете работещите имейл, MX, SPF, DKIM и DMARC записи. За качване на същия хостинг обикновено не е нужна смяна на DNS. Ако се сменя хостинг, планирайте превключването и валиден TLS за www и без www.
6. Проверете HTTP→HTTPS и предпочитания www hostname. Пробвайте стария /bg/info/ceni/ → /ceni/, контактите, петте стари услуги и старите FAQ адреси. Липсващ адрес трябва да дава реален HTTP 404 с нашата страница, а не HTTP 200 с началната.
7. Проверете canonical/OG/sitemap: всички сочат https://www.ego-estetic.com, без chatgpt.site и без preview noindex. Само страницата 404 е noindex. Съществуващите правила покриват 16 намерени стари адреса с двата slash варианта; сравнете ги със Search Console/логовете за допълнителни URL адреси.
8. Проверете на реален телефон и компютър: начална страница → услуга → цени → Superdoc, tel:/mailto: връзки, упътвания, меню, клавиатура, приемане и оттегляне на Google Maps. Тестът не прави реална резервация и не изпраща имейл.
9. Измерете PageSpeed/Core Web Vitals на истинския публичен домейн. Подайте sitemap.xml в Search Console и наблюдавайте 404, индексиране и резервации. Пазете 301 поне година и резервното копие за връщане.

## Бъдещи промени

Изходен проект: https://github.com/HKateliev/dermatology-clinic . Данните са в content.py и site_pages.py, шаблонът — build.py, стилове и JS — dist/assets. Стандартният build изисква Python 3 и Node.js, без npm пакети. За официално публикуване използвайте npm run build:production, след което публикувайте правилния output за конкретния хостинг. Скриптът make_handoff.py създава този пакет. Не качвайте preview dist на официалния домейн: той умишлено е noindex.

Снимките са потвърдени за използване от възложителя. Цените следват само официалната ценова листа на EGO, а не различаващи се стойности от Superdoc. Не са добавени нови медицински протоколи или обещания за резултат. Няма регистрация, контактна форма, аналитични/рекламни скриптове. Публикувана е информация за външното записване и картата, която се зарежда след съгласие.

Пакетът е проверен за съдържание и работещи ресурси; това не е сертификат за правно съответствие, инфраструктурен penetration test или доказателство за измерени Core Web Vitals на бъдещия хостинг.
'''
(DOCS/'START-HERE-BG.md').write_text(readme)
style='body{font:17px/1.65 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 24px;color:#242823}h1,h2{line-height:1.25}h1{color:#b82016}a{color:#a51d15}pre{white-space:pre-wrap}'
html_readme='<!doctype html><html lang="bg"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EGO — инструкции за публикуване</title><style>'+style+'</style><body><pre>'+html.escape(readme)+'</pre></body></html>'
(PUBLIC.parent/'START-HERE.html').write_text(html_readme)
manifest=[]
for file in sorted(PUBLIC.rglob('*')):
 if file.is_file():
  raw=file.read_bytes();manifest.append({'path':file.relative_to(PUBLIC).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(DOCS/'public-file-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Fail if any development/private source or a preview URL leaked into the deployable tree.
for file in PUBLIC.rglob('*'):
 if not file.is_file():continue
 if file.suffix in {'.py','.mjs','.json','.zip'} or 'server' in file.relative_to(PUBLIC).parts:raise SystemExit('Unexpected public file: '+str(file))
 if file.suffix in {'.html','.css','.js','.xml','.txt'}:
  text=file.read_text()
  if 'hkateliev.chatgpt.site' in text or 'appgprj_' in text or 'редакционен проект' in text.lower():raise SystemExit('Preview/private data leaked: '+str(file))
class PublicReferences(HTMLParser):
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);targets=[]
  if tag=='a':targets.append(a.get('href',''))
  if tag in ['img','script']:targets.append(a.get('src',''))
  if tag=='link':targets.append(a.get('href',''))
  if tag=='img':targets.extend(c.strip().split()[0] for c in a.get('srcset','').split(',') if c.strip())
  if tag=='meta' and a.get('property')=='og:image':targets.append(a.get('content',''))
  for target in targets:
   u=urlsplit(target)
   if not u.path or u.scheme in ['mailto','tel','data']:continue
   if u.netloc and u.netloc!='www.ego-estetic.com':continue
   f=PUBLIC/unquote(u.path).lstrip('/')
   if f.is_dir():f=f/'index.html'
   if not f.is_file():raise ValueError('Missing exported public reference: '+target)
for document in PUBLIC.rglob('*.html'):PublicReferences().feed(document.read_text())
archive=DEST/'EGO-website-handoff-2026-11-08.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for file in sorted(PUBLIC.parent.rglob('*')):
  if file.is_file():z.write(file,file.relative_to(DEST))
with zipfile.ZipFile(archive) as z:
 if z.testzip():raise SystemExit('ZIP integrity failed')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'public_files':len(manifest),'pages':34,'indexable_pages':production_validation['sitemap_urls']},ensure_ascii=False))
# The authoring checkout stays a nonindexable review copy.
subprocess.run(['python3','build.py'],cwd=ROOT,check=True)
subprocess.run(['python3','validate.py'],cwd=ROOT,check=True)
