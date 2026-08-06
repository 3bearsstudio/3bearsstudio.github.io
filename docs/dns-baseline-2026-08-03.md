# DNS baseline for `3bears.studio` — captured 2026-08-03, before the Workspace MX cutover

> ## ✅ CUTOVER COMPLETED 2026-08-03 — verified against public DNS
>
> | Check | Result |
> |---|---|
> | `dig MX 3bears.studio` | `1 smtp.google.com.` |
> | `dig TXT` | Google SPF + Google site-verification, **no Cloudflare records left** |
> | `dig A` | all four GitHub Pages IPs intact |
> | `curl https://3bears.studio` | **200** |
> | `curl https://api.3bears.studio/health` | **`{"ok":true}`** |
>
> **The website and the waitlist API were completely unaffected** — checked, not assumed. MX/SPF/DKIM
> records play no part in web traffic, which is why a mail cutover on a domain also serving a site is
> safe *as long as you only touch mail records*.
>
> Record count went **12 → 7** (Cloudflare's five removed by the Disable action) **→ 9** (Google MX +
> Google SPF added). Everything below is the pre-cutover state, kept as the rollback reference.
>
> **✅ Live delivery test passed** — an external message from `philfritzy@gmail.com` to
> `kove@3bears.studio` arrived in the `phil@3bears.studio` inbox in under a minute, tagged
> *External*. That one test proves MX routing, external deliverability, and alias resolution
> together. **Aliases created:** `hello@` · `support@` · `kove@` · `dani@` · `cowatch@` ·
> `sailsuitely@` · `touchpoint@` (7 of the 30 free per user).
>
> ⚠️ **Gmail's "Turn on Gmail — Required" onboarding card was STALE** and appeared after activation
> had already succeeded. Do not trust Google's setup checklists as a state signal — send a real
> external email and watch it arrive. Same discipline as verifying a DB write against the table
> rather than the response code.
>
> **Still outstanding:** DKIM (generate in Admin console → Apps → Google Workspace → Gmail →
> Authenticate email, publish as TXT) and DMARC. Do both before the first bulk send to the waitlist.

**Why this file exists.** On 2026-08-03 the domain moved from Cloudflare Email Routing (forwarding)
to Google Workspace (real mailboxes), which means **deleting and replacing the MX and mail-auth
records**. This is the exact state of the zone immediately *before* that change — the thing to
compare against if mail or the website breaks afterwards, and the thing to restore from if the
cutover has to be rolled back.

Captured from Cloudflare → 3bears.studio → DNS → Records. **12 of 200 records used.**

## The records, and which are load-bearing

| Name | Type | Content | Proxy | Purpose | Survives the cutover? |
|---|---|---|---|---|---|
| `3bears.studio` | A | `185.199.111.153` | **DNS only** | GitHub Pages | ✅ do not touch |
| `3bears.studio` | A | `185.199.108.153` | **DNS only** | GitHub Pages | ✅ do not touch |
| `3bears.studio` | A | `185.199.109.153` | **DNS only** | GitHub Pages | ✅ do not touch |
| `3bears.studio` | A | `185.199.110.153` | **DNS only** | GitHub Pages | ✅ do not touch |
| `api.3bears.studio` | AAAA | `100::` | **Proxied** | waitlist Worker | ✅ do not touch |
| `www.3bears.studio` | CNAME | `3bearsstudio.github.io` | **DNS only** | GitHub Pages | ✅ do not touch |
| `3bears.studio` | MX | `route1.mx.cloudflare.net` | DNS only | Email Routing | ❌ replaced by Google's MX |
| `3bears.studio` | MX | `route2.mx.cloudflare.net` | DNS only | Email Routing | ❌ replaced |
| `3bears.studio` | MX | `route3.mx.cloudflare.net` | DNS only | Email Routing | ❌ replaced |
| `3bears.studio` | TXT | `v=spf1 include:_spf.mx.cloudflare.net ~all` | DNS only | Email Routing SPF | ❌ → `include:_spf.google.com` |
| `cf2024-1._domainkey` | TXT | `v=DKIM1; h=sha256; …` | DNS only | Email Routing DKIM | ❌ → Google-generated DKIM |
| `3bears.studio` | TXT | `google-site-verification=j6YgRMwExml6oKT4GTcZfAyXT7EtVEnpupumdGQPcXE` | DNS only | Workspace domain verification | ✅ keep |

## The Email Routing rules being replaced (captured before disabling)

All five forwarded into **`3bearsstudiollc@gmail.com`** (the studio gmail — *not*
`philfritzy@gmail.com`). ~10 emails delivered in the 7 days before the cutover, so these were live,
not dormant.

| Address | Status | Becomes |
|---|---|---|
| `phil@3bears.studio` | Active | the **primary Workspace user** (the one paid seat) |
| `hello@3bears.studio` | Active | free alias — **published on public pages + privacy policies** |
| `support@3bears.studio` | Active | free alias — **App Store support contact** |
| `kove@3bears.studio` | Active | free alias — waitlist replies |
| `dani@3bears.studio` | Active | free alias **for now** — see the note below |
| Catch-all | **Disabled** (action: Drop) | Workspace has no catch-all by default either — behaviour unchanged |

⚠️ **`dani@` changes behaviour at the cutover.** It used to land in the *shared* studio gmail that
both members could reach; as an alias on Phil's user it lands in **Phil's** inbox only. That is a
deliberate cost decision (a real second user is $8.40/mo). Converting an alias to a real user later
is trivial — delete the alias, create the user with the same address — so revisit it the moment
Dani actually wants her own mailbox.

## 🚨 The two records that must never change

1. **The four apex A records and the `www` CNAME must stay "DNS only" (grey cloud).** Proxying them
   breaks GitHub Pages' ability to issue the HTTPS certificate — for the studio homepage **and every
   app page under the domain**.
2. **`api` must stay Proxied (orange).** A Worker only intercepts proxied traffic; grey-clouding it
   sends the waitlist endpoint to the IPv6 discard prefix and every signup fails.

These two requirements are contradictory on one hostname, which is why the API lives on `api.` — see
`~/appDevelopment/md/static-site-form-backend-cloudflare.md`.

## Why the cutover order is forced

The three MX records and the `cf2024-1._domainkey` TXT show a **🔒 padlock** in Cloudflare's UI:
they are *managed by Email Routing* and cannot be edited or deleted while it is enabled. So:

1. Verify the domain with Google (TXT) — done, safe, changes nothing
2. **Disable Cloudflare Email Routing** — this unlocks the MX records **and kills every forward
   (`hello@`, `support@`, `phil@`, `kove@`) instantly**
3. Add Google's MX records
4. Recreate all addresses as **aliases** on the single Workspace user (free, 30 per user) — NOT as
   additional users, which are billable
5. Then re-establish mail auth against Google: enable **DKIM** in Admin console (Apps → Google
   Workspace → Gmail → Authenticate email), replace the **SPF** TXT with
   `v=spf1 include:_spf.google.com ~all`, and add a **DMARC** record

Steps 2–4 are the only window in which mail bounces. Keep it short.

## Rollback

To go back to forwarding: re-enable Cloudflare Email Routing (it re-creates its own MX/SPF/DKIM
records automatically), delete Google's MX records, and recreate the four forwarding rules. The
Google verification TXT is harmless to leave in place.
