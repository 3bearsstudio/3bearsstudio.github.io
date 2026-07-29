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
because it can read the actual app code. The only handoff is that an app session reports its URL and
the card here gets linked. Do not edit another app's page from here.

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

**Why both files.** Without the italic face the browser fakes italic by skewing the roman. On a
high-contrast display serif that is visibly wrong — real italic letterforms change *shape*, they
don't just lean. Only the hero accent uses it, but that is the most-looked-at type on the page.

`--display` in `:root` is the one place the font stack is defined; Georgia is the fallback because
it is metrically close enough that a slow-connection swap doesn't badly reflow the page.

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
