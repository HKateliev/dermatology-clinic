"""Fail a public-release gate until real practice approvals are recorded."""
from pathlib import Path
import json, re
from datetime import date

ROOT=Path(__file__).resolve().parent
approvals=json.loads((ROOT/'launch-approvals.json').read_text())
inventory=json.loads((ROOT/'page-inventory.json').read_text())
errors=[]
for key in ['practice_details_confirmed','privacy_and_provider_details_confirmed',
            'photo_publication_rights_confirmed','price_scope_confirmed']:
    if approvals.get(key) is not True:errors.append(key)
for item in inventory:
    path=item['url']
    if not item['pending_review'] or path in ['/404/','/poveritelnost/','/uslovia/']:
        continue
    entry=approvals.get('medical_reviews',{}).get(path,{})
    try:
        reviewed=date.fromisoformat(entry.get('date',''))
        valid_date=reviewed<=date.today()
    except ValueError:valid_date=False
    if not (entry.get('reviewer') and valid_date and entry.get('content_sha256')==item['content_sha256']):
        errors.append('Missing exact-content medical review: '+path)
    file=ROOT/'dist'/path.strip('/')/'index.html'
    main=re.search(r'<main[^>]*>(.*?)</main>',file.read_text(),re.S).group(1)
    if re.search(r'редакционен проект|за медицинско потвърждение|преглед: предстои|предстои потвърждение',main,re.I):
        errors.append('Draft notices still present: '+path)
for path in ['poveritelnost','uslovia']:
    main=re.search(r'<main[^>]*>(.*?)</main>',(ROOT/'dist'/path/'index.html').read_text(),re.S).group(1)
    if re.search(r'за потвърждение|предстои|настоящият текст е проект',main,re.I):
        errors.append('Incomplete legal page: /'+path+'/')
result={'ready_for_public_release':not errors,'blockers':errors}
(ROOT/'release-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
