"""Explicit preview/production output; never index a review deployment by accident."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['preview', 'production'], default='preview')
parser.add_argument('--origin')
parser.add_argument('--output', default='dist')
args = parser.parse_args()
MODE = args.mode
ORIGIN = (args.origin or ('https://www.ego-estetic.com' if MODE == 'production' else
          'https://ego-dermatology-varna.hkateliev.chatgpt.site')).rstrip('/')
parsed = urlsplit(ORIGIN)
if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
    raise SystemExit('Origin must be an HTTPS origin without a path, query, credentials or fragment.')
if MODE == 'production' and parsed.hostname not in {'www.ego-estetic.com', 'ego-estetic.com'}:
    raise SystemExit('Production origin must be the confirmed practice domain.')
OUT = (ROOT / args.output).resolve()
if OUT == ROOT or ROOT not in OUT.parents:
    raise SystemExit('Output must be a subdirectory of this checkout.')
REVIEWS = json.loads((ROOT / 'launch-approvals.json').read_text())

def approved(path, content_hash):
    """A recorded review must name a reviewer and date, not merely set a boolean."""
    entry = REVIEWS['medical_reviews'].get(path, {})
    return bool(entry.get('reviewer') and entry.get('date') and entry.get('content_sha256') == content_hash)

def indexable(path, draft, content_hash):
    return MODE == 'production' and path != '/404/' and (not draft or approved(path, content_hash))
