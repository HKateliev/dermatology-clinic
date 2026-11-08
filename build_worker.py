"""Embed the checked static output into a small dependency-free Sites Worker."""
from pathlib import Path
import base64, hashlib, json, sys

ROOT=Path(__file__).resolve().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist'
info=json.loads((out/'build-info.json').read_text())
headers={}
for line in (out/'_headers').read_text().splitlines()[1:]:
    if not line.startswith(' '):break
    name,value=line.strip().split(':',1)
    headers[name]=value.strip()
types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8',
       '.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp',
       '.xml':'application/xml; charset=utf-8','.txt':'text/plain; charset=utf-8'}
assets={}
for file in sorted(out.rglob('*')):
    relative=file.relative_to(out)
    if not file.is_file() or relative.parts[0]=='server' or file.suffix not in types:continue
    if file.name.startswith('_'):continue
    data=file.read_bytes();route='/'+relative.as_posix()
    if file.name=='index.html':route=route.removesuffix('index.html')
    noindex=file.suffix=='.html' and b'content="noindex,follow"' in data
    assets[route]={'data':base64.b64encode(data).decode(),'type':types[file.suffix],
                   'etag':'"'+hashlib.sha256(data).hexdigest()+'"','noindex':noindex}
redirects={line.split()[0]:line.split()[1] for line in (out/'_redirects').read_text().splitlines() if line.strip()}
source=(ROOT/'worker/index.js').read_text()
for key,value in [('ASSETS',assets),('REDIRECTS',redirects),('SECURITY',headers),('BUILD',info)]:
    source=source.replace('__EGO_'+key+'__',json.dumps(value,ensure_ascii=True,separators=(',',':')))
target=out/'server/index.js';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
print('Generated Worker for',len(assets),'public resources;',target.stat().st_size,'bytes; no runtime bindings.')
