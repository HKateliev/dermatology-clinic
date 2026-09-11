# EGO — dermatologist-led practice site

34 Bulgarian HTML pages, shared CSS and progressive JS, no framework dependency. The 11 September visual revision uses the supplied EGO red logo, local authentic photographs and a shorter homepage (323 versus 586 visible main-content words in browser inspection). Build with `python build.py`; validate with `python validate.py`. Source content is edited in `content.py`; layout is in `build.py` and `dist/assets/style.css`. Static output is tracked intentionally.

## Verified facts

Checked 11 September 2026 against https://www.ego-estetic.com/bg/ and https://superdoc.bg/lekar/galina-moneva . Contact details match. Public profile verifies 30+ years, children, medical education 1989, specialty 1994, EGO since 2019. No numeric reviews, awards, memberships, or current equipment inventory invented. Prices are source snapshots in EUR. EU currency source: https://economy-finance.ec.europa.eu/euro/eu-countries-and-euro/bulgaria-and-euro_en .

## Required practice review before original-domain release

- Medical pages and patient articles are editorial drafts, marked visibly and noindex. Do not remove review notices or change indexation until the practice has reviewed the exact copy. Confirm authorship, reviewer and dates; do not imply prior doctor approval.
- Full opening hours need confirmation; existing site only exposes Monday 09:00–16:00.
- Wart price differs: official 60 EUR, Superdoc 40 EUR. No selected price published.
- Confirm xanthelasma size units, hair-removal zone prices, filler quantity/product, scope of 80 EUR laser rejuvenation and 200 EUR eye contour, biopsy histology inclusion, package eligibility. Preserve historical source prices in content verification notes, not as validated offers.
- Legal entity, registration data, controller details, lawful bases, retention periods and processing arrangements need final verification. Legal pages are drafts where applicable.
- Authentic photographs are local JPEG assets captured from the browser-rendered original media in the professional Superdoc gallery, with no generative changes. Portrait original 778×1000, saved displayed 728×936; practice photo 1200×769; treatment room 1200×800. Original download events did not complete; browser capture excludes the browser chrome and cursor. Confirm publication rights and current appearance of the practice with the doctor.
- Photo sources: https://superdoc.bg/photos/doctors/large/gPzrgfoqJcxtBZqFZu9W0Gny4B0uNt17fGagWExl.jpeg ; https://superdoc.bg/photos/doctors/large/tw2cRewNeQHn06J3pzzJw2msnc6IuvRw68xo3JTE.jpeg ; https://superdoc.bg/photos/doctors/large/GDFofcqxZyARl1DJWMCILqq487vYRWvF7JtpCyH6.jpeg . No equipment model or inventory claims inferred from images.
- Supplied logo PNG is preserved exactly. CSS frames the main EGO mark for navigation. Theme uses red #c9261b (darkened for white-text contrast), warm white and light peach/olive surfaces. Favicon uses its circular O motif.

- Social metadata uses the authentic primary doctor portrait. The previous plum social-card asset is retained in source history; no new generated photography is used. Detail pages without a unique primary image omit inherited social images.

## Migration

All discovered key Bulgarian old URLs, including slash variants, are in `redirect-map.json` and `dist/_redirects` with 301 status. 404.html is provided. Do not redirect all legacy content to the homepage. Original domain/DNS/hosting was not changed. Before migration, compare against Search Console and server logs for any additional indexed or backlink-bearing URLs, including language variants. Change ORIGIN to the confirmed production origin, rebuild canonical tags and sitemap, preserve direct 301 mappings, and validate real response statuses on the selected host. Confirm custom-host support for Cloudflare-style _redirects/_headers.

Medical drafts are deliberately excluded from sitemap and use noindex,follow. Core approved-fact pages are crawlable; private Sites audience additionally restricts access. The private preview domain is self-canonical, never misleadingly set to the existing live domain.

## Privacy and accessibility

No contact form, tracking, analytics, or marketing pixels. Google Maps only loads after explicit consent; equal preference controls, native accessible dialog, persistent browser-local choice and revoke option. External booking on Superdoc. Click-to-call telephone and directions links. Semantic headings, focus styles, skip link, native details, 44px+ primary targets, reduced motion, mobile menu and sticky actions. Primary text colors validated for AA contrast. No claim of certified WCAG conformance.

## Validation limitations

Static checks cover all local links, anchors, image dimensions, JSON-LD parsing, redirect destinations and primary contrast. JavaScript passes syntax validation. Desktop browser QA confirmed all four homepage image instances load and no horizontal overflow at 1363px. At 390px the mobile menu opens and navigates to Prices; the price document has matching client and scroll widths (no horizontal overflow). A dependency-free preview server and dev-only mobile QA route are included. Core Web Vitals are not field-measured. Review images on real devices and measure LCP/INP/CLS before original-domain release. Do not claim performance targets achieved.

## GitHub handoff

Repository: https://github.com/HKateliev/dermatology-clinic . This repository contains the current EGO website source, static output and original local image assets. Sites publishing is managed separately; GitHub updates do not automatically deploy to Sites. GitHub Pages is not configured.

For local review: `npm run dev`; no npm packages need installing. For static hosting use `python3 build.py` (or `npm run build`) and publish `dist`. The development-only mobile QA route is not in the deployment output.
