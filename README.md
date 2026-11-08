# EGO · д-р Галина Монева — website handoff

34 Bulgarian pages, responsive static HTML/CSS/JavaScript and a dependency-free Cloudflare Worker for Sites. External booking is through Superdoc. No production npm packages, database, contact form or analytics.

**The site is technically ready to hand to the existing maintainer.**

- [Current handoff report](docs/HANDOFF-REPORT-2026-11-08.md)
- [Destination launch checklist](docs/LAUNCH-CHECKLIST.md)
- [Static validation](validation-report.json)
- [Published private Site HTTP check](published-audit-report.json)
- [Technical handoff gate](release-status.json)
- [Earlier audit history](docs/RELEASE-AUDIT-2026-11-08.md)

## Build and check

Python 3 and Node.js are sufficient; no npm install is required.

```sh
npm run build
npm run check
npm run check:release
```

`content.py` contains the source-based services and official prices; `site_pages.py` the patient FAQ and website notices; `build.py` the layout/metadata. Styles and client JS are in `dist/assets`. Output HTML is intentionally tracked. `worker/index.js` and `build_worker.py` generate ignored `dist/server/index.js`, embedding the checked public resources without an asset binding.

The default build is the existing private review origin: all pages are noindex and its sitemap is empty. Production uses `https://www.ego-estetic.com`, with 33 indexable content pages and a noindex 404:

```sh
npm run build:production
```

Do not copy a preview `dist` onto the real domain. The source manifest retains the existing Sites project ID and selects Worker ESM by omitting `static`. Sites requires explicit publishing; it is not automatically synced with GitHub. The practice domain has not been switched by this project.

## Handoff ZIP

```sh
python3 make_handoff.py --output-dir /absolute/output/directory --source-ref main
```

The ZIP includes `public_html/` (ready production-domain files with Apache/LiteSpeed `.htaccess`) and `handoff/` (Bulgarian instructions, Nginx examples, redirect map, manifests, results and a standalone Worker alternative). Only the contents of `public_html/` belong in the public web root. Do not publish the whole ZIP, source, documentation, backups or the alternative Worker file as a static asset.

The authoring checkout is restored to nonindexable preview after packaging. The final host needs its actual server configuration and TLS checks. Apache and Nginx were not installed in the creation environment, so their examples require validation by the maintainer on the destination. This is a static site, not a WordPress import/theme or the old CMS admin panel.

## Content and confirmations

The user confirmed image use and that the clinic's own latest price list is correct. Prices use only https://www.ego-estetic.com/bg/info/ceni/ : 33 published positions, including the exact xanthelasma size units. No biopsy price from Superdoc or invented hair-removal zone prices remain. The detailed service copy and patient FAQ were reduced to the existing published services and answers. Added clinical protocols were removed; there is no invented doctor-review byline or fake testimonial/rating.

The current original privacy URL was checked in the browser and has a title but no policy text. The new notice uses public practice identity/contact details and the actual website data flow. No company form or EIK was invented. The clinic/maintainer must confirm the exact legal controller identity and chosen hosting/log-retention information before the public switch. This does not prevent handing over the completed files and does not imply legal certification.

The consent-controlled Google map, safe external booking links, keyboard focus, mobile navigation, semantic metadata, source-safe redirects, correct 404 and security headers are implemented. `worker/validate.mjs` checks the serving bundle; `validate.py` checks static content and resources. `audit_http.py --origin https://www.ego-estetic.com` can verify the destination after installation. Managed preview has a development-only `/_qa/http-audit/` route for its isolated namespace; QA routes are not in the deployment or handoff.

The image assets are authentic local photographs with WebP variants and a responsive portrait; the original supplied logo is retained. Normal builds use committed assets. Only regenerating raster derivatives with `prepare_assets.py` requires Pillow and the listed system fonts. The 1200×630 social card uses the actual portrait/logo.

Core Web Vitals have not been field-measured. The reports explicitly distinguish tested code/Chromium/HTTP behaviour from real-device, cross-browser, infrastructure and legal checks.
