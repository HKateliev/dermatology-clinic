# EGO · д-р Галина Монева — Варна

34 Bulgarian pages, static HTML/CSS/JavaScript, external booking through Superdoc. No production framework, npm packages, database, contact form or analytics. The original supplied logo and authentic practice photos are retained.

**The technical audit is complete; public release still requires the practice confirmations described below.**

- [Full audit and verified results — 8 November 2026](docs/RELEASE-AUDIT-2026-11-08.md)
- [Launch checklist and outstanding confirmations](docs/LAUNCH-CHECKLIST.md)
- [Machine-readable static validation](validation-report.json)
- [Supervised preview HTTP verification](http-audit-report.json)
- [Public-release gate result](release-status.json)

## Develop and validate

Python 3 and Node.js are sufficient for the normal build; no npm installation is needed. Source content is in `content.py`; templates and metadata are in `build.py`; authored styles/JS are under `dist/assets`. Generated static output is intentionally tracked.

```sh
npm run build
npm run check
npm run dev
```

The default is **preview mode** on the existing private Sites origin. Every page has noindex and the preview sitemap is empty. This prevents an accidentally exposed review copy from competing with the real practice domain. It is not an access-control mechanism; Sites audience stays private separately.

`npm run check:http` runs read-only HTTP checks against a local preview. Managed preview runs in a separate namespace: if shell loopback is unavailable, the development-only `/_qa/http-audit/` page executes the checks next to that server. Its route, mobile QA shell and Python/source files are not part of `dist` or public deployment.

## Production

`npm run build:production` first checks the real approvals in `launch-approvals.json`, then builds for `https://www.ego-estetic.com` and validates the output. It intentionally fails while physician review, legal/provider details, photo rights and price scope remain unconfirmed. It never fabricates an approval.

For a nondeployed inspection of domain-specific output:

```sh
python3 build.py --mode production --output audit-production
python3 validate.py --output audit-production
```

That inspection bypasses no publishing control and is not a release approval. Its unapproved medical pages remain noindex. Only reviewed pages become indexable; the public-release gate also checks draft notices. The review hash covers the main content excluding the variable source-links block and matches across preview/production. Return to `npm run build` to restore the tracked review output after inspection.

The final host must actually implement `_headers`, `_redirects`, correct 404 responses and HTTPS, or translate the configuration into its server equivalent. There is a CSP meta fallback, but framing protection and HSTS require actual response headers. Do not assume that copying files to any host applies these files automatically. Core Web Vitals have not been field-measured.

## Content and migration

Verified contacts, procedures, biography and clear EUR prices were compared with the existing EGO site and Superdoc on 8 November 2026. A wart is 60 EUR on EGO and 40 EUR on Superdoc: the site now uses EGO's own figure and records the discrepancy in the audit. Unclear xanthelasma units, filler volume, biopsy histology and hair-removal zone prices are not invented. Only Monday 09:00–16:00 is publicly verified.

Medical pages and articles are drafts pending an actual physician review. Existing absolute promises of scar-free, risk-free or universally harmless treatment are not repeated. There are no fabricated ratings, qualifications, equipment inventories or treatment results. Photograph publication rights and final legal/controller details still require practice confirmation.

`redirect-map.json` covers the 16 discovered old addresses with slash/no-slash variants, 32 direct 301 rules. Search Console/server logs may reveal more URLs. No DNS or hosting changes to the current practice domain have been performed. Original-domain release requires a backup and final-host checks in the launch checklist.

## Images and privacy

WebP variants and a responsive portrait are generated from the exact existing local JPEG photographs by `prepare_assets.py` (requires Pillow for asset regeneration only; normal builds use committed assets). The social card uses the actual portrait and logo. There are no generated people or patient before/after images. Source photographs come from the public Superdoc profile; their publication rights must be confirmed by the practice.

The browser makes no automatic external image/font/analytics requests. The map is created only after explicit consent, with a persistent directions link and withdrawal control. Consent can work in memory if browser storage is blocked; stored consent expires after 180 days. Google receives connection data only when its service is used. Site policy drafts must be finalised for the chosen actual hosting and business arrangements.

## GitHub and Sites

Repository: https://github.com/HKateliev/dermatology-clinic . The existing Site identity in `.openai/hosting.json` is preserved. GitHub and Sites do not automatically synchronise; updating either does not imply publication of the other. GitHub Pages is not configured. The public practice domain has not been switched.
