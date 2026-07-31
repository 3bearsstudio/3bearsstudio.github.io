# 3bears.studio — the studio homepage

The public homepage for **3 Bears Studio LLC**. One self-contained `index.html`, served by
GitHub Pages at <https://3bears.studio>.

- **Repo:** `3bearsstudio/3bearsstudio.github.io` (public — GitHub Pages needs it)
- **Local copy:** `~/appDevelopment/3bears-studio-site/`
- **Custom domain:** `CNAME` holds `3bears.studio`. DNS lives in Cloudflare and the records must
  stay **"DNS only" (grey cloud)** — proxying blocks GitHub from issuing the HTTPS certificate.
- **`.nojekyll`** is required, or GitHub silently drops files/folders beginning with `_`.

## Read this first

**<~/appDevelopment/md/studio-identity-web-standards.md>** is the canonical source for the legal
entity name, the public contact address, the brand↔repo map, and the publish runbook. Do not
re-derive any of those facts from memory — one of them shipped wrong once, which is why the file
exists.

Two rules that bite most often:

- The legal name is **`3 Bears Studio LLC`** — the **numeral 3**, never "Three".
- **Never advertise client / contract / custom development work** on this page, in any form. A
  services section went live on 2026-07-28 and was removed the same day. See the standards doc.

## Who owns what

This page is owned by the **studio/LLC session**: entity facts, positioning, and the product cards.

**Each app's own session owns its own page** (`3bears.studio/<app>/` and everything under it),
because it can read the actual app code.

**Clarified 2026-07-31 — the rule is about CROSS-APP edits, not about the studio session.**

- ✅ The **studio/LLC session is the orchestrator** and may edit **any** app's page. It holds the
  cross-cutting context (the standards doc, the shared API, the design systems), so shared work like
  the waitlist form lands there rather than being re-explained to five sessions.
- ✅ An app's own session may edit its own page.
- 🚫 **One app's session must never touch another app's page.** The CoWatch session does not edit
  Kove's site. That is the failure this rule exists to prevent.

When the studio session does edit an app page, **commit and push before handing back**, so the app's
own session never starts from a stale tree.

## Serving it locally

```bash
python3 -m http.server 8099
```

Then open <http://localhost:8099>. A plain `file://` open also works, but the font will not load
under some browsers' local-file rules, so prefer the server.

## Vendored assets

Per the standards doc §4, the page must make **no third-party requests** — nothing from a host we
don't control. Anything external is therefore committed into this repo and referenced by a relative
path. There is **no bundler, no npm, and no lockfile**, so nothing here updates itself: keeping
these current is a manual job.

| File | What | Version | Licence |
|---|---|---|---|
| `fonts/Fraunces.woff2` | Display serif, roman. Variable: `opsz` 9–144, `wght` 300–800. Latin subset, 66 KB | Google Fonts v38 | SIL OFL 1.1 — `fonts/Fraunces-OFL.txt` |
| `fonts/Fraunces-Italic.woff2` | The **true** italic of the same face, 80 KB | Google Fonts v38 | same |
| `vendor/anime.esm.min.js` | Animation engine. Drives the device-fan scroll reveal. 116 KB on disk, **40 KB gzipped** on the wire | anime.js **4.5.0** | MIT — `vendor/anime-LICENSE.md` |

**Updating Anime.js** is manual — there is no lockfile. Replace the file, replace
`vendor/anime-LICENSE.md`, and bump the version in this table. Check the v4 changelog
first: the page imports `animate`, `stagger` and `onScroll` as named ESM exports.

## Screenshots

`assets/shots/<app>/` holds the device screenshots, as **720px-wide WebP** (~30–65 KB each).
Raw simulator captures are ~2 MB PNGs and must **never** be committed — git keeps them forever,
so deleting them later does not shrink the repo.

```bash
python3 tools/prep-shots.py <raw-capture-dir> assets/shots/<app>
```

`tools/prep-shots.py` resizes and converts; run it before the first commit, not after. Its
docstring covers usage, failure modes, and why it must not be used on App Store submission
screenshots (Apple wants full-resolution PNGs at exact device sizes — this script destroys both).

**Only apps with real screenshots get the featured treatment.** Kove and Sail Suitely have
captures, so they get a fan of three devices beside their copy; the rest stay text-only in the
"Also in the works" row until their captures exist. Do not invent a mockup to fill the gap —
that would undo the entire point of the section.

**Why both files.** Without the italic face the browser fakes italic by skewing the roman. On a
high-contrast display serif that is visibly wrong — real italic letterforms change *shape*, they
don't just lean. Only the hero accent uses it, but that is the most-looked-at type on the page.

`--display` in `:root` is the one place the font stack is defined; Georgia is the fallback because
it is metrically close enough that a slow-connection swap doesn't badly reflow the page.

## Claude Design — the design systems

`tools/build-design-systems.py` generates the **design-system card bundles** that Claude Design
(the separate `Design` app) attaches to anything it generates, so its output uses our real fonts
and colours instead of inventing a look. **Six systems, 33 cards**, first published 2026-07-31:

| System | Covers | Consistent with the others? |
|---|---|---|
| **3 Bears Studio** | this homepage **and every app page under the domain** | **Yes — it is one website** |
| Kove · Sail Suitely · CoWatch · TouchPoint CRM · Bear Books | each app's own look | **No — they are different products** |

That split is the point: the app *pages* are one site and must cohere; the *apps* should not look
like each other.

```bash
python3 tools/build-design-systems.py     # -> build/design-systems/<slug>/*.html  (gitignored)
```

**Every token is read out of a real source file** — the script's docstring lists exactly which one
per system, including `TimeOfDayPalette.swift` for Kove's four times of day and `Theme.swift` for
Bear Books. It invents nothing. When a palette changes, re-run it and re-push; do not hand-edit a
card.

Publishing is done by Claude through the **DesignSync** tool, not by this script:
`create_project` → `finalize_plan` (`writes: ["*.html"]`, `localDir` = that system's folder) →
`write_files` → `register_assets`.

Two traps, both hit on the first build:

- **Font stacks in these cards use SINGLE quotes.** They get interpolated into `style="…"`
  attributes, and a double quote ends the attribute early — silently dropping `font-size` and
  everything after it. First build had every type specimen at the same size.
- **Cards must render offline**, so Fraunces is inlined as a base64 data URI. That makes the type
  card ~198 KB; `MAX_CARD_BYTES` fails the build before it reaches DesignSync's 256 KiB limit.

## Rules the page has to keep passing

These are cheap to break and were each verified when last changed:

- **No third-party requests.** `grep -oiE '(src|href)="https?://[^"]*' index.html` should return
  nothing outside `3bears.studio`.
- **Works with JavaScript disabled.** Every rule that *hides* content is prefixed with `.js` or
  `.js-hero`, and those classes are only added by script once the reveal observer is actually live.
  If you add an animation, hide the element the same way — otherwise a JS failure leaves content
  permanently invisible.
- **`prefers-reduced-motion`** switches the entire motion layer off: no snow, no progress rail, no
  transforms, everything visible and static.
- **No horizontal overflow from 360px to 1440px.** Decorative layers may extend past the viewport,
  but only inside an `overflow:hidden` parent.
- **Footer carries** `© <year> 3 Bears Studio LLC` and `Apopka, Florida, USA`.

## Deploying

Commit and push to `main`. GitHub Pages rebuilds in roughly a minute.

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://3bears.studio/
```
