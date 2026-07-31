#!/usr/bin/env python3
"""
Build Claude Design "design system" card bundles for 3 Bears Studio and each app.

WHAT THIS IS
------------
Claude Design (the separate `Design` app / claude.ai/design) can attach a *design
system* to anything it generates, so output uses our real fonts and colours
instead of inventing a look. A design system is a folder of small, self-contained
preview HTML files; each one's FIRST LINE carries an `@dsCard` marker naming the
group it belongs to. Claude's Design System pane renders each file as a card.

This script generates those bundles from tokens that were READ OUT OF THE REAL
SOURCE FILES (see SOURCES below) — it never invents a colour. Re-run it whenever
a palette changes, then re-push with the DesignSync tool.

USAGE
-----
    python3 tools/build-design-systems.py [--out DIR]

Writes DIR/<system-slug>/... (default DIR = build/design-systems, gitignored).
Prints a summary of every file written. No network access, no dependencies
beyond the standard library.

Then, to publish (Claude does this via the DesignSync tool, not this script):
    DesignSync create_project  -> projectId
    DesignSync finalize_plan   -> planId       (writes: "<slug>/**")
    DesignSync write_files     (localPath = the generated files)
    DesignSync register_assets (one card per file)

SOURCES — where every token below came from. Keep this list accurate; it is the
only thing that makes the output verifiable.
    3 Bears Studio ... 3bears-studio-site/index.html          :root + .btn/.kicker
    Kove (web) ....... kove/index.html                        :root
    Kove (app) ....... Anchor/iOS/Anchor/Anchor/Appearance/TimeOfDayPalette.swift
    Sail Suitely ..... sail-suitely-site/index.html           :root
    CoWatch .......... cowatch-site/index.html                :root
    TouchPoint CRM ... touchpoint-crm-site/styles.css         :root + dark override
    Bear Books ....... Bear Books/BearBooks/Core/Theme.swift  (Color(red:g:b:) -> hex)

WHAT MUST NOT GO IN HERE
------------------------
* No invented colours, fonts or components. If it is not in a source file above,
  it does not belong in a card. A design system that lies is worse than none.
* No business data, no private records, no customer content. These bundles are
  uploaded to a Claude Design project — treat them as publishable.
* No third-party asset URLs. Cards must render offline; embed everything.
"""

from __future__ import annotations

import argparse
import base64
import html
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# NOTE: family names are quoted with SINGLE quotes on purpose. These stacks get
# interpolated into `style="..."` attributes, and a double quote there terminates
# the attribute early — silently discarding font-size, weight and everything after
# it. That bug shipped once: every type specimen rendered at the same size.
SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, "
        "Arial, sans-serif")

# Max bytes for one card. The DesignSync file cap is 256 KiB; stay clear of it.
MAX_CARD_BYTES = 240 * 1024


# ─────────────────────────────────────────────────────────────────────────────
# Token model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Swatch:
    name: str
    hex: str
    note: str = ""


@dataclass
class System:
    slug: str
    name: str
    tagline: str
    # Card chrome
    page_bg: str
    page_fg: str
    muted: str
    line: str
    # Type
    display_stack: str
    display_label: str
    body_stack: str = SANS
    body_label: str = "System sans (San Francisco / Segoe / Roboto)"
    # Content
    colors: list[Swatch] = field(default_factory=list)
    colors_dark: list[Swatch] = field(default_factory=list)
    radii: list[tuple[str, str]] = field(default_factory=list)
    button_primary: tuple[str, str] = ("", "")     # (bg, fg)
    button_secondary_border: str = ""
    shadow: str = ""
    gradients: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # (css family name, style, weight, repo-relative woff2) — embedded as a data
    # URI so cards render the real face offline. Cards must make no network calls.
    font_files: list[tuple[str, str, str, str]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# The systems. Every value traced to a source file — see SOURCES in the docstring.
# ─────────────────────────────────────────────────────────────────────────────

STUDIO = System(
    slug="3-bears-studio",
    name="3 Bears Studio",
    tagline="The studio brand — 3bears.studio and every app page under it.",
    page_bg="#070d1a", page_fg="#f5f8fc", muted="#8fa3bd", line="rgba(143,216,234,.22)",
    display_stack="'Fraunces', Georgia, 'Iowan Old Style', 'Times New Roman', serif",
    display_label='Fraunces (self-hosted, SIL OFL) — roman + TRUE italic',
    font_files=[
        ("Fraunces", "normal", "100 900", "fonts/Fraunces.woff2"),
        ("Fraunces", "italic", "100 900", "fonts/Fraunces-Italic.woff2"),
    ],
    colors=[
        Swatch("night",   "#070d1a", "page ground, hero"),
        Swatch("deep",    "#0f2740"),
        Swatch("arctic",  "#14304d"),
        Swatch("aurora",  "#7fe3c4", "primary accent / primary button"),
        Swatch("aurora2", "#9db8ff", "focus ring"),
        Swatch("foam",    "#8fd8ea"),
        Swatch("snow",    "#f5f8fc", "body ground"),
        Swatch("paper",   "#ffffff"),
        Swatch("ink",     "#16202e", "body text"),
        Swatch("muted",   "#55637a"),
        Swatch("kicker",  "#1a6390", "links"),
        Swatch("line",    "#dbe5f0"),
    ],
    radii=[("buttons", "999px"), ("cards", "18px"), ("chips", "999px")],
    button_primary=("#7fe3c4", "#06251c"),
    button_secondary_border="rgba(207,234,245,.38)",
    shadow="0 1px 2px rgba(16,32,52,.05), 0 8px 24px rgba(16,32,52,.06)",
    notes=[
        "Fraunces is SELF-HOSTED from the repo. Never load a font from a CDN — "
        "the site makes zero third-party requests and that is an invariant.",
        "Use the TRUE italic, never a synthesized slant; a faux oblique looks "
        "wrong on a display serif.",
        "A film-grain layer sits over the whole page at low opacity.",
        "Everything must survive JS being off, honour prefers-reduced-motion, "
        "and never scroll horizontally between 360px and 1440px.",
    ],
)

KOVE = System(
    slug="kove",
    name="Kove",
    tagline="Calm focus, screen-time blocking and habits. Ocean at night.",
    page_bg="#0b1426", page_fg="#eaf6fb", muted="#93aec4", line="rgba(143,216,234,.20)",
    display_stack=SANS, display_label="System sans — no display face; the imagery carries the brand",
    colors=[
        Swatch("midnight",  "#0b1426", "hero ground"),
        Swatch("wave-deep", "#123f60"),
        Swatch("wave",      "#2b7bb0", "primary"),
        Swatch("wave-ink",  "#1d5c88", "links"),
        Swatch("foam",      "#8fd8ea", "focus ring"),
        Swatch("cream",     "#eaf6fb"),
        Swatch("ink",       "#16202e"),
        Swatch("muted",     "#4c5870"),
        Swatch("paper",     "#ffffff"),
        Swatch("wash",      "#f3f8fc", "body ground"),
        Swatch("line",      "#dce6f0"),
        Swatch("coral",     "#e2674b", "attention / limits"),
        Swatch("kelp",      "#2f8f6a", "success / streaks"),
    ],
    radii=[("buttons", "999px"), ("cards", "18px")],
    button_primary=("#2b7bb0", "#ffffff"),
    button_secondary_border="rgba(143,216,234,.38)",
    shadow="0 1px 2px rgba(16,32,52,.05), 0 8px 24px rgba(16,32,52,.06)",
    gradients=[
        # Anchor/iOS/.../TimeOfDayPalette.swift — bgTop -> bgBottom, then accent.
        ("Dawn",  "linear-gradient(160deg,#2A1C33,#3D2A3E)"),
        ("Day",   "linear-gradient(160deg,#0A1C34,#0E3048)"),
        ("Dusk",  "linear-gradient(160deg,#12122E,#241830)"),
        ("Night", "linear-gradient(160deg,#080D22,#0D1030)"),
    ],
    notes=[
        "The APP shifts palette through the day — dawn / day / dusk / night — "
        "interpolating between keyframes. Accents in order: #F0A57C, #5FA8D3, "
        "#E8826B, #B6A8F5. Stars only appear at night.",
        "Screen-time data never leaves the device. Never imply otherwise in "
        "marketing copy or imagery.",
        "App Store screenshots must show the REAL app. Frames and backgrounds "
        "may be designed; the screen inside them may not be invented.",
    ],
)

SAIL = System(
    slug="sail-suitely",
    name="Sail Suitely",
    tagline="Luxury cruise discovery — suite classes and ultra-luxury lines.",
    page_bg="#0A1730", page_fg="#F5F1E8", muted="rgba(245,241,232,.68)",
    line="rgba(209,173,102,.22)",
    display_stack="'Iowan Old Style', Georgia, 'Times New Roman', serif",
    display_label="Iowan Old Style / Georgia — a quiet book serif, not a display face",
    colors=[
        Swatch("navy",        "#0F1F3D"),
        Swatch("navy-deep",   "#0A1730", "page ground"),
        Swatch("navy-soft",   "#16294a", "surfaces"),
        Swatch("gold",        "#D1AD66", "primary accent"),
        Swatch("gold-deep",   "#997838"),
        Swatch("gold-bright", "#E4C784", "links, focus ring"),
        Swatch("cream",       "#F5F1E8", "body text"),
    ],
    radii=[("buttons", "4px"), ("cards", "8px"), ("device frame", "46px")],
    button_primary=("#D1AD66", "#0A1730"),
    button_secondary_border="rgba(209,173,102,.42)",
    shadow="0 26px 55px rgba(0,0,0,.55)",
    notes=[
        "Restraint is the brand. Gold is an accent on deep navy — never a fill, "
        "never a gradient wash. If it looks like a casino, it is wrong.",
        "Tight corner radii (4–8px) read as considered; big soft rounding reads "
        "as consumer app and fights the positioning.",
        "Co-created with Monica (contractor, not an owner).",
    ],
)

COWATCH = System(
    slug="cowatch",
    name="CoWatch",
    tagline="A shared film / TV / anime watchlist built for two people.",
    page_bg="#0B0B11", page_fg="#F4F4F7", muted="#B4B4C2", line="#2A2A36",
    display_stack=SANS,
    display_label="System sans, heavy weights — the gradient wordmark is the brand mark",
    colors=[
        Swatch("violet",      "#8B6CFF", "primary"),
        Swatch("violet-deep", "#6B4EF6"),
        Swatch("pink",        "#FF6B9D"),
        Swatch("pink-deep",   "#FF5C8A"),
        Swatch("bg",          "#0B0B11", "page ground"),
        Swatch("bg2",         "#0E0E14"),
        Swatch("surface",     "#16161F"),
        Swatch("surface2",    "#1C1C27"),
        Swatch("line",        "#2A2A36"),
        Swatch("text-primary",   "#F4F4F7"),
        Swatch("text-secondary", "#B4B4C2"),
        Swatch("text-tertiary",  "#8A8A99"),
    ],
    radii=[("buttons", "999px"), ("cards", "14px"), ("focus ring", "6px")],
    button_primary=("#8B6CFF", "#0B0B11"),
    button_secondary_border="#2A2A36",
    shadow="0 12px 32px rgba(0,0,0,.45)",
    gradients=[("Brand gradient", "linear-gradient(120deg,#8B6CFF,#FF6B9D)")],
    notes=[
        "⚠️ PROVISIONAL. CoWatch is still being reworked and its name may change. "
        "Re-run this script before trusting these tokens.",
        "The wordmark is the brand gradient clipped to text. Use the gradient for "
        "the mark and small accents — not as a page-wide background.",
        "iPhone only. It has no Android build; never claim one.",
    ],
)

TOUCHPOINT = System(
    slug="touchpoint-crm",
    name="TouchPoint CRM",
    tagline="Business-card scanning and follow-up tracking. Local-first.",
    page_bg="#FFFFFF", page_fg="#1A1C1E", muted="#545E6B", line="#E4E9F0",
    display_stack=SANS, display_label="System sans throughout — a working tool, not a brand piece",
    colors=[
        Swatch("blue",     "#1565C0", "primary"),
        Swatch("blue-700", "#0D47A1"),
        Swatch("teal",     "#00897B", "secondary"),
        Swatch("teal-400", "#4DB6AC"),
        Swatch("fire",     "#FF6B35", "attention / overdue"),
        Swatch("ink",      "#1A1C1E"),
        Swatch("muted",    "#545E6B"),
        Swatch("bg",       "#FFFFFF"),
        Swatch("surface",  "#F6F9FD"),
        Swatch("border",   "#E4E9F0"),
    ],
    colors_dark=[
        Swatch("blue",     "#6BA6F5"),
        Swatch("blue-700", "#4D8AE0"),
        Swatch("teal",     "#4DB6AC"),
        Swatch("ink",      "#E7ECF3"),
        Swatch("muted",    "#A2AEBD"),
        Swatch("bg",       "#0E141C"),
        Swatch("surface",  "#141C26"),
        Swatch("card",     "#161F2B"),
        Swatch("border",   "#26313F"),
    ],
    radii=[("cards", "16px"), ("small", "10px")],
    button_primary=("#1565C0", "#ffffff"),
    button_secondary_border="#E4E9F0",
    shadow="0 1px 2px rgba(16,24,40,.06), 0 12px 32px rgba(16,24,40,.06)",
    notes=[
        "The ONLY system here that ships a real light mode and a real dark mode. "
        "Design both; do not assume dark.",
        "iPhone AND Android — the Kotlin codebase is real (~26.5k lines). Layouts "
        "should survive both platforms' conventions.",
    ],
)

BEARBOOKS = System(
    slug="bear-books",
    name="Bear Books",
    tagline="The studio's own bookkeeping Mac app. Internal, never marketed.",
    page_bg="#0f1720", page_fg="#eef4fa", muted="#93a6bb", line="rgba(140,180,215,.22)",
    display_stack=SANS, display_label="System sans — a native macOS app, it should look native",
    colors=[
        # Bear Books/BearBooks/Core/Theme.swift, Color(red:green:blue:) -> hex,
        # each channel round(x * 255).
        Swatch("ocean",    "#1A6BAD", "deep sea blue — primary"),
        Swatch("aurora",   "#2EB89E", "teal-green"),
        Swatch("sky",      "#5CADE6"),
        Swatch("sand",     "#EDDBB8"),
        Swatch("positive", "#299E6B", "money in / good"),
        Swatch("negative", "#D1594D", "money out / attention"),
        Swatch("warning",  "#E69E33"),
    ],
    radii=[("cards", "12px")],
    button_primary=("#1A6BAD", "#ffffff"),
    button_secondary_border="rgba(140,180,215,.30)",
    shadow="0 10px 28px rgba(0,0,0,.35)",
    notes=[
        "⚠️ INTERNAL TOOL. Bear Books holds the studio's real financial records. "
        "It is never marketed, never screenshotted publicly, and nothing "
        "generated against this system should contain real figures.",
        "Positive/negative/warning are semantic — money in, money out, attention. "
        "Never use them decoratively.",
    ],
)

SYSTEMS = [STUDIO, KOVE, SAIL, COWATCH, TOUCHPOINT, BEARBOOKS]


# ─────────────────────────────────────────────────────────────────────────────
# Card rendering
# ─────────────────────────────────────────────────────────────────────────────

_FONT_CACHE: dict[str, str] = {}


def font_face_css(s: System, repo_root: Path, italic: bool = False) -> str:
    """@font-face rules with the woff2 inlined as a data URI (no network calls)."""
    if not s.font_files:
        return ""
    out = []
    for family, style, weight, rel in s.font_files:
        if style == "italic" and not italic:
            continue
        path = repo_root / rel
        if not path.exists():
            raise SystemExit(f"missing font file: {path} (referenced by {s.slug})")
        if rel not in _FONT_CACHE:
            _FONT_CACHE[rel] = base64.b64encode(path.read_bytes()).decode("ascii")
        out.append(
            f"@font-face{{font-family:'{family}';font-style:{style};"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{_FONT_CACHE[rel]}) format('woff2')}}")
    return "\n".join(out)


def shell(s: System, group: str, title: str, subtitle: str, body: str,
          repo_root: Path, italic: bool = False) -> str:
    """Wrap card content in a self-contained document with the @dsCard marker."""
    return f"""<!-- @dsCard group="{html.escape(group)}" name="{html.escape(title)}" subtitle="{html.escape(subtitle)}" -->
<!doctype html>
<meta charset="utf-8">
<title>{html.escape(s.name)} — {html.escape(title)}</title>
<style>
{font_face_css(s, repo_root, italic)}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:36px 40px;background:{s.page_bg};color:{s.page_fg};
       font-family:{s.body_stack};line-height:1.55;-webkit-font-smoothing:antialiased}}
  h1{{font-family:{s.display_stack};font-size:30px;line-height:1.1;margin:0 0 4px;
     letter-spacing:-.02em;font-weight:600}}
  .sub{{color:{s.muted};font-size:13.5px;margin:0 0 26px}}
  .rule{{height:1px;background:{s.line};margin:0 0 26px}}
  .grid{{display:grid;gap:14px}}
  code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}}
</style>
<h1>{html.escape(title)}</h1>
<p class="sub">{html.escape(subtitle)}</p>
<div class="rule"></div>
{body}
"""


def card_colors(s: System, swatches: list[Swatch], title: str, subtitle: str,
                repo_root: Path) -> str:
    cells = []
    for sw in swatches:
        note = f'<div style="color:{s.muted};font-size:11.5px">{html.escape(sw.note)}</div>' if sw.note else ""
        cells.append(f"""
    <div>
      <div style="height:74px;border-radius:10px;background:{sw.hex};
                  border:1px solid {s.line}"></div>
      <div style="margin-top:8px;font-size:13px;font-weight:600">{html.escape(sw.name)}</div>
      <div style="font-size:12px;color:{s.muted}"><code>{sw.hex}</code></div>
      {note}
    </div>""")
    body = ('<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(132px,1fr))">'
            + "".join(cells) + "</div>")
    return shell(s, "Colors", title, subtitle, body, repo_root)


def card_type(s: System, repo_root: Path) -> str:
    rows = [
        ("Display / hero", 52, s.display_stack, 600, "-.03em"),
        ("Section heading", 30, s.display_stack, 600, "-.02em"),
        ("Subheading", 20, s.body_stack, 600, "-.01em"),
        ("Body", 16, s.body_stack, 400, "0"),
        ("Small / caption", 13, s.body_stack, 400, "0"),
        ("Eyebrow", 11, s.body_stack, 700, ".10em"),
    ]
    out = []
    for label, size, stack, weight, ls in rows:
        upper = "text-transform:uppercase;" if label == "Eyebrow" else ""
        out.append(f"""
    <div style="padding:14px 0;border-bottom:1px solid {s.line}">
      <div style="font-size:11px;color:{s.muted};letter-spacing:.08em;
                  text-transform:uppercase;margin-bottom:6px">{html.escape(label)} · {size}px</div>
      <div style="font-family:{stack};font-size:{size}px;font-weight:{weight};
                  letter-spacing:{ls};{upper}line-height:1.15">Three bears, one studio</div>
    </div>""")
    # If the system ships a real italic, show it next to a faux slant. The rule
    # "never use a synthesized oblique" only lands if you can see the difference.
    if any(style == "italic" for _f, style, _w, _p in s.font_files):
        out.append(f"""
    <div style="padding:16px 0;border-bottom:1px solid {s.line}">
      <div style="font-size:11px;color:{s.muted};letter-spacing:.08em;
                  text-transform:uppercase;margin-bottom:10px">True italic vs faux slant</div>
      <div style="font-family:{s.display_stack};font-size:30px;font-style:italic;
                  font-weight:600;line-height:1.2">Three bears &mdash; the real italic</div>
      <div style="font-family:{s.display_stack};font-size:30px;font-weight:600;
                  transform:skewX(-12deg);transform-origin:left;line-height:1.2;
                  opacity:.55;margin-top:6px">Three bears &mdash; a skewed fake</div>
      <div style="font-size:12.5px;color:{s.muted};margin-top:10px">
        Use the top one. The lower is a geometric skew &mdash; note the broken
        stroke weights and the unchanged letterforms.</div>
    </div>""")

    body = (f'<p style="margin:0 0 18px;font-size:13.5px;color:{s.muted}">'
            f'<strong style="color:{s.page_fg}">Display:</strong> {html.escape(s.display_label)}<br>'
            f'<strong style="color:{s.page_fg}">Body:</strong> {html.escape(s.body_label)}</p>'
            + "".join(out))
    return shell(s, "Type", "Type scale",
                 "Display face, body face, and the ramp between them.", body,
                 repo_root, italic=True)


def card_components(s: System, repo_root: Path) -> str:
    bg, fg = s.button_primary
    radius = dict(s.radii).get("buttons", "10px")
    card_radius = dict(s.radii).get("cards", "14px")
    body = f"""
  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:30px">
    <span style="display:inline-flex;align-items:center;gap:9px;border-radius:{radius};
                 padding:13px 24px;font-weight:700;font-size:15px;background:{bg};color:{fg}">
      Primary action</span>
    <span style="display:inline-flex;align-items:center;gap:9px;border-radius:{radius};
                 padding:13px 24px;font-weight:700;font-size:15px;
                 border:1px solid {s.button_secondary_border};color:{s.page_fg}">
      Secondary</span>
    <span style="display:inline-flex;align-items:center;border-radius:999px;padding:6px 14px;
                 font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                 border:1px solid {s.line};color:{s.muted}">Eyebrow chip</span>
  </div>

  <div style="display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))">
    <div style="border:1px solid {s.line};border-radius:{card_radius};padding:20px;
                box-shadow:{s.shadow}">
      <div style="font-family:{s.display_stack};font-size:19px;font-weight:600;margin-bottom:6px">
        Card</div>
      <div style="font-size:13.5px;color:{s.muted}">
        Radius {card_radius}, 1px hairline, the system's own shadow.</div>
    </div>
    <div style="border:1px solid {s.line};border-radius:{card_radius};padding:20px;
                box-shadow:{s.shadow}">
      <div style="font-family:{s.display_stack};font-size:19px;font-weight:600;margin-bottom:6px">
        Second card</div>
      <div style="font-size:13.5px;color:{s.muted}">
        Cards sit on the page ground, not on a tinted panel.</div>
    </div>
  </div>

  <div style="margin-top:28px;font-size:12.5px;color:{s.muted}">
    <strong style="color:{s.page_fg}">Radii</strong> &nbsp;
    {" &nbsp;·&nbsp; ".join(f"{html.escape(k)} <code>{html.escape(v)}</code>" for k, v in s.radii)}
    <br><strong style="color:{s.page_fg}">Shadow</strong> &nbsp;<code>{html.escape(s.shadow)}</code>
  </div>
"""
    return shell(s, "Components", "Buttons & cards",
                 "The recurring pieces, at their real sizes.", body, repo_root)


def card_gradients(s: System, repo_root: Path) -> str:
    cells = []
    for label, css in s.gradients:
        cells.append(f"""
    <div>
      <div style="height:112px;border-radius:12px;background:{css};
                  border:1px solid {s.line}"></div>
      <div style="margin-top:8px;font-size:13px;font-weight:600">{html.escape(label)}</div>
    </div>""")
    body = ('<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr))">'
            + "".join(cells) + "</div>")
    title = "Time of day" if s.slug == "kove" else "Gradients"
    sub = ("The app's ground shifts through the day — these are the four keyframes."
           if s.slug == "kove" else "Brand gradients.")
    return shell(s, "Brand", title, sub, body, repo_root)


def card_rules(s: System, repo_root: Path) -> str:
    items = "".join(
        f'<li style="margin-bottom:12px">{html.escape(n)}</li>' for n in s.notes)
    body = (f'<ul style="margin:0;padding-left:20px;font-size:14.5px;max-width:60ch">{items}</ul>'
            f'<p style="margin-top:26px;font-size:12px;color:{s.muted}">'
            f'Generated by <code>tools/build-design-systems.py</code> in the '
            f'3bears-studio-site repo, from the real source files. Do not hand-edit '
            f'these cards — change the source, then re-run.</p>')
    return shell(s, "Brand", "Rules", "Constraints that are not negotiable.", body, repo_root)


def card_overview(s: System, repo_root: Path) -> str:
    chips = "".join(
        f'<span style="width:34px;height:34px;border-radius:8px;background:{sw.hex};'
        f'border:1px solid {s.line};display:inline-block"></span>' for sw in s.colors[:9])
    body = f"""
  <p style="font-size:16px;max-width:58ch;margin:0 0 24px">{html.escape(s.tagline)}</p>
  <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:26px">{chips}</div>
  <div style="font-family:{s.display_stack};font-size:44px;font-weight:600;
              letter-spacing:-.03em;line-height:1.05;max-width:16ch">{html.escape(s.name)}</div>
"""
    return shell(s, "Brand", "Overview", s.tagline, body, repo_root)


def build(s: System, root: Path, repo_root: Path) -> list[tuple[str, str, str]]:
    """Write one system's cards. Returns (path, group, title) for registration."""
    d = root / s.slug
    d.mkdir(parents=True, exist_ok=True)
    made: list[tuple[str, str, str]] = []

    def w(rel: str, content: str, group: str, title: str) -> None:
        (d / rel).write_text(content, encoding="utf-8")
        size = (d / rel).stat().st_size
        if size > MAX_CARD_BYTES:
            raise SystemExit(
                f"{s.slug}/{rel} is {size/1024:.0f} KiB, over the "
                f"{MAX_CARD_BYTES/1024:.0f} KiB card cap — drop an embedded font")
        made.append((f"{s.slug}/{rel}", group, title))

    w("overview.html", card_overview(s, repo_root), "Brand", "Overview")
    w("type.html", card_type(s, repo_root), "Type", "Type scale")
    w("colors.html",
      card_colors(s, s.colors, "Palette",
                  "Every colour the product actually uses, with its token name.",
                  repo_root),
      "Colors", "Palette")
    if s.colors_dark:
        w("colors-dark.html",
          card_colors(s, s.colors_dark, "Palette — dark mode",
                      "The prefers-color-scheme: dark overrides.", repo_root),
          "Colors", "Palette — dark mode")
    w("components.html", card_components(s, repo_root), "Components", "Buttons & cards")
    if s.gradients:
        title = "Time of day" if s.slug == "kove" else "Gradients"
        w("gradients.html", card_gradients(s, repo_root), "Brand", title)
    w("rules.html", card_rules(s, repo_root), "Brand", "Rules")
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="build/design-systems",
                    help="output directory (default: build/design-systems)")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    root = Path(args.out).resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    total = 0
    for s in SYSTEMS:
        made = build(s, root, repo_root)
        total += len(made)
        print(f"{s.name:<18} {len(made):>2} cards  ->  {root / s.slug}")
        for path, group, title in made:
            print(f"    [{group:<11}] {title:<22} {path}")
    print(f"\n{total} cards across {len(SYSTEMS)} systems in {root}")


if __name__ == "__main__":
    main()
