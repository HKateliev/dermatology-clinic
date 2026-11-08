"""Technical handoff gate for the user-authorised, source-based website."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
confirmation=json.loads((ROOT/'launch-approvals.json').read_text())
inventory=json.loads((ROOT/'page-inventory.json').read_text())
report=json.loads((ROOT/'validation-report.json').read_text())
errors=[]
for key in ['practice_details_confirmed','photo_publication_rights_confirmed','price_scope_confirmed']:
 if confirmation.get(key) is not True:errors.append(key)
if report.get('errors'):errors.append('Static validation errors')
for item in inventory:
 if item['url']=='/404/':continue
 file=ROOT/'dist'/('index.html' if item['url']=='/' else item['url'].strip('/')+'/index.html')
 text=file.read_text()
 if re.search(r'редакционен проект|за медицинско потвърждение|преглед: предстои|за потвърждение преди|Lorem ipsum',text,re.I):
  errors.append('Unfinished public content: '+item['url'])
 if item.get('pending_review'):errors.append('Draft route: '+item['url'])
prices=(ROOT/'dist/ceni/index.html').read_text()
if 'Superdoc¹' in prices or 'Биопсия — по' in prices:errors.append('Nonofficial price mixed into official price list')
result={'ready_for_handoff':not errors,'technical_blockers':errors,
 'basis':'Official services and prices; existing photo use confirmed by the user; no claim of physician review of new medical advice.',
 'installer_checks_before_public_switch':['Back up old website and its database, preserve email/DNS settings.','Confirm full controller/provider identity from the clinic records; the old privacy page is empty.','Apply destination-specific headers/301/404/HTTPS and run live checks on ego-estetic.com.'],
 'certifications':{'legal_compliance_certified':False,'medical_review_of_new_clinical_content_claimed':False,'every_possible_web_test_claimed':False}}
(ROOT/'release-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
