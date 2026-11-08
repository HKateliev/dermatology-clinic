"""Offline release regression checks, using only the Python standard library."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote, urljoin
from collections import Counter
import argparse, json, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='dist')
args = parser.parse_args()
OUT = ROOT / args.output
info = json.loads((OUT/'build-info.json').read_text())
origin = info['origin']

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links=[]; self.ids=[]; self.h1=0; self.images=[]; self.schemas=[]
        self.meta={}; self.canonicals=[]; self.title=''; self.in_title=False
        self.in_schema=False; self.schema=''; self.problems=[]; self.anchors=[]
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
        if 'style' in a or any(k.startswith('on') for k in a): self.problems.append('Inline style/event handler')
        if tag=='html' and a.get('lang')!='bg': self.problems.append('Missing Bulgarian language')
        if tag=='title': self.in_title=True
        if tag=='h1': self.h1+=1
        if tag=='img':
            self.images.append(a)
            self.links.append(a.get('src',''))
            for candidate in a.get('srcset','').split(','):
                if candidate.strip(): self.links.append(candidate.strip().split()[0])
        if tag=='meta':
            key=a.get('name') or a.get('property') or a.get('http-equiv','').lower()
            if key:
                if key in self.meta: self.problems.append('Duplicate meta: '+key)
                self.meta[key]=a.get('content','')
        if tag=='a' and 'href' in a:
            self.links.append(a['href']);self.anchors.append(a)
        if tag=='link':
            if a.get('rel')=='canonical': self.canonicals.append(a.get('href'))
            if a.get('rel') in ('stylesheet','icon'): self.links.append(a.get('href',''))
        if tag=='iframe' and a.get('src'): self.problems.append('Map loaded before consent')
        if tag=='script':
            if a.get('src'): self.links.append(a['src'])
            elif a.get('type')=='application/ld+json': self.in_schema=True; self.schema=''
            else: self.problems.append('Inline executable script')
    def handle_data(self, data):
        if self.in_schema:self.schema+=data
        if self.in_title:self.title+=data
    def handle_endtag(self, tag):
        if tag=='script' and self.in_schema:
            self.schemas.append(json.loads(self.schema)); self.in_schema=False
        if tag=='title':self.in_title=False

pages={p:Page(p.read_text()) for p in OUT.rglob('*.html')}
errors=[];warnings=[];titles=[];descriptions=[];canonicals=[]
for file,page in pages.items():
    label=str(file.relative_to(OUT));text=file.read_text()
    errors.extend([label,p] for p in page.problems)
    if page.h1!=1:errors.append([label,'H1 count',page.h1])
    if len(page.ids)!=len(set(page.ids)):errors.append([label,'Duplicate ID'])
    if len(page.canonicals)!=1:errors.append([label,'Canonical count'])
    expected='/' if label=='index.html' else '/'+label.removesuffix('index.html')
    if label=='404.html':expected='/404/'
    if page.canonicals!=[origin+expected]:errors.append([label,'Incorrect canonical'])
    if page.meta.get('og:url')!=origin+expected:errors.append([label,'Incorrect OG URL'])
    for key in ['description','robots','og:title','og:description','og:image','twitter:card','twitter:image','content-security-policy']:
        if not page.meta.get(key):errors.append([label,'Missing metadata',key])
    if len(page.title)>70:warnings.append([label,'Long title',len(page.title)])
    if len(page.meta.get('description',''))>180:warnings.append([label,'Long description'])
    if info['mode']=='preview' and 'noindex' not in page.meta.get('robots',''):errors.append([label,'Indexable preview'])
    if label!='404.html':
        titles.append(page.title);descriptions.append(page.meta.get('description'));canonicals.extend(page.canonicals)
    for image in page.images:
        if not all(image.get(k) for k in ['alt','width','height','src']):errors.append([label,'Image metadata'])
        if urlsplit(image.get('src','')).netloc:errors.append([label,'External image'])
    for anchor in page.anchors:
        u=urlsplit(anchor['href'])
        if u.scheme=='http' or u.scheme in ('javascript','data'):errors.append([label,'Unsafe link',anchor['href']])
        if anchor.get('target')=='_blank' and not {'noopener','noreferrer'}<=set(anchor.get('rel','').split()):errors.append([label,'Unprotected external window'])
    for target in page.links+[page.meta.get('og:image',''),page.meta.get('twitter:image','')]:
        u=urlsplit(target)
        if u.netloc and u.netloc!=urlsplit(origin).netloc:continue
        if u.scheme and not u.netloc:continue
        path=urlsplit(urljoin('https://local'+expected,target)).path
        p=OUT/unquote(path.lstrip('/'))
        if p.is_dir():p=p/'index.html'
        if not p.is_file():errors.append([label,'Missing local resource',target])
        elif u.fragment and p in pages and unquote(u.fragment) not in pages[p].ids:errors.append([label,'Missing anchor',target])
    for schema in page.schemas:
        if schema.get('@context')!='https://schema.org':errors.append([label,'Invalid JSON-LD context'])
        if 'aggregateRating' in json.dumps(schema):errors.append([label,'Unverified rating markup'])
for label,values in [('title',titles),('description',descriptions),('canonical',canonicals)]:
    for value,n in Counter(values).items():
        if n>1:errors.append(['Duplicate '+label,value])
redirects=json.loads((ROOT/'redirect-map.json').read_text())
for old,new in redirects.items():
    if new in redirects:errors.append([old,'Redirect chain'])
    if not (OUT/new.lstrip('/')/'index.html').is_file():errors.append([old,'Missing redirect target'])
sitemap=ET.fromstring((OUT/'sitemap.xml').read_text())
locations=[node.text for node in sitemap.findall('.//{*}loc')]
if len(locations)!=len(set(locations)):errors.append(['Duplicate sitemap URL'])
for loc in locations:
    p=OUT/urlsplit(loc).path.lstrip('/')/'index.html'
    if not loc.startswith(origin+'/') or p not in pages:errors.append(['Invalid sitemap URL',loc])
    elif 'noindex' in pages[p].meta['robots']:errors.append(['Sitemap contains noindex page',loc])
if info['mode']=='preview' and locations:errors.append(['Preview sitemap must be empty'])
headers=(OUT/'_headers').read_text()
for required in ['Content-Security-Policy:','X-Content-Type-Options: nosniff','Referrer-Policy: no-referrer','X-Frame-Options: SAMEORIGIN','Strict-Transport-Security:']:
    if required not in headers:errors.append(['Missing security header',required])
if any(token in headers for token in ['unsafe-inline','unsafe-eval','script-src *']):errors.append(['Unsafe CSP'])
for file in OUT.rglob('*'):
    if file.suffix in {'.html','.js','.json','.css'}:
        if re.search(r'github_pat_|gh[pousr]_[A-Za-z0-9]{20,}|BEGIN .*PRIVATE KEY',file.read_text()):errors.append(['Secret-like token',str(file)])
report={'mode':info['mode'],'origin':origin,'unique_pages':info['page_count'],'html_documents':len(pages),'legacy_redirects':len(redirects),'sitemap_urls':len(locations),'errors':errors,'warnings':warnings,'browser_qa':'See docs/HANDOFF-REPORT-2026-11-08.md; not inferred from static checks.','security_scope':'Static source and HTTP/browser behaviour; not a hosting-account penetration test.','core_web_vitals':'Not field-measured. LCP/INP/CLS must be measured on the final public host.'}
(ROOT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
