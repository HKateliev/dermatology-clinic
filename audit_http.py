"""Read-only checks against a running preview or the eventual public host."""
import argparse, json, urllib.request, urllib.error, concurrent.futures, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--origin',default='http://127.0.0.1:4173')
args=parser.parse_args()
origin=args.origin.rstrip('/')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
opener=urllib.request.build_opener(NoRedirect)
def request(path,method='GET'):
    try:
        response=opener.open(urllib.request.Request(origin+path,method=method),timeout=15)
    except urllib.error.HTTPError as error:response=error
    except urllib.error.URLError as error:return 0, {'X-Audit-Error':str(error)}
    return response.status,response.headers
errors=[]
initial_status,initial_headers=request('/')
if initial_status==0:
    result={'origin':origin,'verified':False,'errors':[initial_headers['X-Audit-Error']]}
    (ROOT/'http-audit-report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));sys.exit(1)
inventory=json.loads((ROOT/'page-inventory.json').read_text())
paths=[row['url'] for row in inventory if row['url']!='/404/']
def page(path):
    status,headers=request(path)
    issues=[]
    if status!=200:issues.append([path,'Expected 200',status])
    for header in ['Content-Security-Policy','X-Content-Type-Options','Referrer-Policy','Permissions-Policy','Strict-Transport-Security']:
        if not headers.get(header):issues.append([path,'Missing HTTP header',header])
    return issues
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for issues in pool.map(page,paths):errors.extend(issues)
redirects=json.loads((ROOT/'redirect-map.json').read_text())
for old,new in redirects.items():
    status,headers=request(old)
    if status!=301 or headers.get('Location') not in [new,origin+new]:errors.append([old,'Incorrect 301',status,headers.get('Location')])
for path in ['/missing-page-for-release-audit/','/.git/config','/content.py','/server/index.js','/_headers','/index.php','/source.php']:
    status,_=request(path)
    if status not in ([404] if path=='/missing-page-for-release-audit/' else [403,404]):errors.append([path,'Expected missing/blocked response',status])
status,headers=request('/ceni')
if status!=301 or headers.get('Location') not in ['/ceni/',origin+'/ceni/']:errors.append(['/ceni','Missing canonical slash redirect'])
status,_=request('/','POST')
if status not in [403,405]:errors.append(['POST /','Expected method rejection',status])
status,headers=request('/bg/info/ceni/?audit=1')
if status!=301 or headers.get('Location') not in ['/ceni/?audit=1',origin+'/ceni/?audit=1']:errors.append(['Redirect query preservation'])
report={'origin':origin,'content_pages_checked':len(paths),'legacy_redirects_checked':len(redirects),'errors':errors,
        'scope':'Responses from this exact origin, not assumed to apply to any other deployment.'}
(ROOT/'http-audit-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
