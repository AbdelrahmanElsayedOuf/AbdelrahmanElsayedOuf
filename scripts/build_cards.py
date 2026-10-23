#!/usr/bin/env python3
"""
Glass design system for the GitHub profile README (iOS-inspired, light + dark).

Every card is a plain static SVG: no filters, no blur, no external fonts or
images, so the profile loads fast. The "frosted glass" look comes from soft
radial-gradient colour blobs under a translucent panel with a specular
highlight and a hairline border.

Usage:
  python3 scripts/build_cards.py            # build every card
  python3 scripts/build_cards.py --stats    # only refresh the stats card
                                                    # (uses GITHUB_TOKEN + GITHUB_USER)
"""
import json, os, sys, urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
USER = os.environ.get("GITHUB_USER", "AbdelrahmanElsayedOuf")

# ─────────────────────────── design tokens ───────────────────────────
FONT = ("-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', "
        "'Segoe UI Variable', 'Segoe UI', Inter, Roboto, 'Helvetica Neue', Arial, sans-serif")

# iOS system colours (light / dark variants)
IOS = {
    "blue":   ("#007AFF", "#0A84FF"),
    "indigo": ("#5856D6", "#5E5CE6"),
    "purple": ("#AF52DE", "#BF5AF2"),
    "pink":   ("#FF2D55", "#FF375F"),
    "orange": ("#FF9500", "#FF9F0A"),
    "yellow": ("#FFCC00", "#FFD60A"),
    "green":  ("#34C759", "#30D158"),
    "teal":   ("#30B0C7", "#40C8E0"),
    "cyan":   ("#32ADE6", "#64D2FF"),
}
# tile gradients (top-left → bottom-right), like iOS app icons
TILE = {
    "blue":   ("#5AC8FA", "#007AFF"),
    "indigo": ("#7D7AFF", "#4B47D6"),
    "purple": ("#DA8FFF", "#9F44D3"),
    "pink":   ("#FF7A9A", "#FF2D55"),
    "orange": ("#FFC15C", "#FF8A00"),
    "green":  ("#6EE28B", "#28B44A"),
    "teal":   ("#6FE0EE", "#21A3BA"),
    "yellow": ("#FFE36B", "#FFB800"),
}

THEMES = {
    "light": dict(
        base="#F2F2F7", glass="#FFFFFF", glass_o=".58", stroke="#FFFFFF", stroke_o=".95",
        hair="#000000", hair_o=".07", spec_o=".65", ink="#1C1C1E", ink2="#6E6E73", ink3="#8E8E93",
        chip="#FFFFFF", chip_o=".72", chip_stroke="#000000", chip_stroke_o=".06", blob_o=".55", idx=0),
    "dark": dict(
        base="#0B0B0F", glass="#1C1C1E", glass_o=".55", stroke="#FFFFFF", stroke_o=".16",
        hair="#FFFFFF", hair_o=".08", spec_o=".10", ink="#F5F5F7", ink2="#AEAEB2", ink3="#8E8E93",
        chip="#FFFFFF", chip_o=".08", chip_stroke="#FFFFFF", chip_stroke_o=".10", blob_o=".50", idx=1),
}

# Lucide-style line icons on a 24×24 grid (stroke-based, no emoji)
ICONS = {
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M8 7V5.5A2.5 2.5 0 0 1 10.5 3h3A2.5 2.5 0 0 1 16 5.5V7M3 13h18"/>',
    "award": '<circle cx="12" cy="9" r="6"/><path d="M8.6 13.9 7 22l5-3 5 3-1.6-8.1"/>',
    "cap": '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12.2V17c3 2.7 9 2.7 12 0v-4.8M22 10v6"/>',
    "drop": '<path d="M12 2.7S18 9.3 18 14a6 6 0 0 1-12 0c0-4.7 6-11.3 6-11.3Z"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1Z"/>',
    "receipt": '<path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2Z"/><path d="M9 8h6M9 12h6M9 16h3.5"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14ZM4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M16 4.1a4 4 0 0 1 0 7.8M22 21a7 7 0 0 0-4.5-6.5"/>',
    "server": '<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6.5h.01M7 17.5h.01"/>',
    "layout": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M9 21V9"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.8"/><rect x="14" y="3" width="7" height="7" rx="1.8"/><rect x="3" y="14" width="7" height="7" rx="1.8"/><rect x="14" y="14" width="7" height="7" rx="1.8"/>',
    "plug": '<path d="M9 2v6M15 2v6M6 8h12v3a6 6 0 0 1-12 0V8ZM12 17v5"/>',
    "branch": '<circle cx="6" cy="5.5" r="2.5"/><circle cx="6" cy="18.5" r="2.5"/><circle cx="18" cy="8" r="2.5"/><path d="M6 8v8M18 10.5c0 4.5-7 3.5-11 6"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3.5"/><path d="M8 10.5V17M8 7.2v.01M12 17v-6.5M12 13.5a2.5 2.5 0 0 1 5 0V17"/>',
    "chat": '<path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.6-5A8.5 8.5 0 1 1 21 11.5Z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "pin": '<path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    "code": '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    "star": '<path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.3L12 17.1l-5.6 3 1.1-6.3L2.9 9.4l6.3-.9L12 2.8Z"/>',
    "folder": '<path d="M3 6.5A2.5 2.5 0 0 1 5.5 4H9l2 2.5h7.5A2.5 2.5 0 0 1 21 9v8.5a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5v-11Z"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "sparkles": '<path d="M12 3l1.8 4.9L19 10l-5.2 2.1L12 17l-1.8-4.9L5 10l5.2-2.1L12 3ZM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "ticket": '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4V8Z"/><path d="M14 6v2.5M14 10.8v2.4M14 15.5V18"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
}

# ───────────────────────────── primitives ─────────────────────────────

def tw(s, size, bold=True):
    """Conservative text width estimate for system sans fonts."""
    k = 0.61 if bold else 0.575
    narrow = sum(1 for c in s if c in "il.,:;|'!tfjrI ·")
    return (len(s) - narrow * 0.45) * size * k


def wrap(text, size, maxw, bold=False):
    lines, cur = [], ""
    for w in text.split():
        nxt = (cur + " " + w).strip()
        if tw(nxt, size, bold) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def T(x, y, s, size, fill, weight=600, anchor="start", ls=None, op=None):
    a = f' letter-spacing="{ls}"' if ls else ""
    o = f' fill-opacity="{op}"' if op else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}"{o} text-anchor="{anchor}"{a}>{escape(s)}</text>')


def icon(name, x, y, size, color="#FFFFFF", sw=2):
    s = size / 24
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


class Doc:
    def __init__(self, w, h, theme, title):
        self.w, self.h, self.t, self.title = w, h, THEMES[theme], title
        self.defs, self.body, self.n = [], [], 0

    def uid(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def grad(self, a, b, x2=1, y2=1):
        gid = self.uid("g")
        self.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                         f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')
        return f"url(#{gid})"

    def glass(self, x, y, w, h, r, blobs):
        """A frosted iOS-style panel. blobs = [(color_key, cx%, cy%, r%)] relative to the panel."""
        if not hasattr(self, "glass_args"):
            self.glass_args = (r, blobs)
        t = self.t
        cid = self.uid("c")
        self.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
        out = [f'<g clip-path="url(#{cid})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t["base"]}"/>']
        for key, cx, cy, rr in blobs:
            col = IOS[key][t["idx"]]
            rid = self.uid("r")
            self.defs.append(f'<radialGradient id="{rid}"><stop offset="0" stop-color="{col}" stop-opacity="{t["blob_o"]}"/>'
                             f'<stop offset=".55" stop-color="{col}" stop-opacity="{float(t["blob_o"]) * .35:.2f}"/>'
                             f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
            R = rr * max(w, h)
            out.append(f'<circle cx="{x + cx * w:.0f}" cy="{y + cy * h:.0f}" r="{R:.0f}" fill="url(#{rid})"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t["glass"]}" fill-opacity="{t["glass_o"]}"/>')
        spec = self.uid("s")
        self.defs.append(f'<linearGradient id="{spec}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="{t["spec_o"]}"/>'
                         f'<stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{spec})"/></g>')
        rim = self.uid("m")
        self.defs.append(f'<linearGradient id="{rim}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["stroke"]}" stop-opacity="{t["stroke_o"]}"/>'
                         f'<stop offset=".5" stop-color="{t["stroke"]}" stop-opacity="{float(t["stroke_o"]) * .3:.2f}"/>'
                         f'<stop offset="1" stop-color="{t["stroke"]}" stop-opacity="{float(t["stroke_o"]) * .7:.2f}"/></linearGradient>')
        out.append(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r - .5}" fill="none" stroke="{t["hair"]}" stroke-opacity="{t["hair_o"]}"/>')
        out.append(f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{w - 3}" height="{h - 3}" rx="{r - 1.5}" fill="none" stroke="url(#{rim})" stroke-width="1.5"/>')
        self.body.append("".join(out))

    def tile(self, x, y, s, color, ico, glyph=None):
        """iOS app-icon style squircle with a white line icon."""
        a, b = TILE[color]
        g = self.grad(a, b)
        r = s * 0.27
        self.body.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{r:.1f}" fill="{g}"/>'
                         f'<rect x="{x + .75}" y="{y + .75}" width="{s - 1.5}" height="{s - 1.5}" rx="{r - .75:.1f}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.5"/>')
        if glyph:
            self.body.append(T(x + s / 2, y + s / 2 + s * .16, glyph, s * .42, "#FFFFFF", 800, "middle"))
        else:
            gs = s * .52
            self.body.append(icon(ico, x + (s - gs) / 2, y + (s - gs) / 2, gs, "#FFFFFF", 2.1))

    def chip(self, x, y, label, size=13, h=28, pad=12, dot=None, ico=None, color=None):
        t = self.t
        extra = (14 if dot else 0) + (size + 6 if ico else 0)
        w = tw(label, size) + pad * 2 + extra
        self.body.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t["chip"]}" fill-opacity="{t["chip_o"]}" '
                         f'stroke="{t["chip_stroke"]}" stroke-opacity="{t["chip_stroke_o"]}"/>')
        tx = x + pad
        if dot:
            self.body.append(f'<circle cx="{tx + 4}" cy="{y + h / 2}" r="4" fill="{IOS[dot][t["idx"]]}"/>')
            tx += 14
        if ico:
            self.body.append(icon(ico, tx, y + (h - size) / 2, size, color or t["ink2"], 2.2))
            tx += size + 6
        self.body.append(T(tx, y + h / 2 + size * .36, label, size, t["ink"], 650))
        return w

    def render(self):
        mt, mb = getattr(self, "mt", 0), getattr(self, "mb", 0)
        H = self.h + mt + mb
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{H}" viewBox="0 {-mt} {self.w} {H}" '
                f'role="img" aria-label="{escape(self.title)}" font-family="{escape(FONT)}">'
                f'<title>{escape(self.title)}</title><defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')

    def render_slice(self, x, y, w, h, title):
        """Render a crop of this panel. Slices of one panel tile back into a single seamless glass section."""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x} {y} {w} {h}" '
                f'role="img" aria-label="{escape(title)}" font-family="{escape(FONT)}">'
                f'<title>{escape(title)}</title><defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


# ─────────────────────────────── content ───────────────────────────────
W = 1000

PROJECTS = [
    dict(slug="belkhedma", short="Marketplace", name="Belkhidmah ABP", kicker="Home-services marketplace", color="indigo", ico="home",
         regions=[("SA", "Saudi Arabia", "green")],
         desc="A unified marketplace aggregating hourly labor, monthly contracts, medical staff and mediation providers into one app — with escrow payments released on delivery.",
         tags=["ASP.NET Zero", "Angular", "Flutter", "Dynamics 365", "Redis", "HyperPay"], blobs=[("indigo", .1, .2, .5), ("purple", .9, .9, .5)]),
    dict(slug="einvoicing", short="Invoicing", name="E-Invoicing", kicker="Invoicing & billing system", color="orange", ico="receipt",
         regions=[("EG", "Egypt", "pink"), ("SA", "Saudi Arabia", "green")],
         desc="Clean-architecture Web API automating invoice generation, customer billing and payment tracking for trips, reservations and receipt vouchers.",
         tags=["ASP.NET Core", "EF Core", "SQL Server", "JWT", "AutoMapper"], blobs=[("orange", .1, .2, .5), ("pink", .9, .9, .5)]),
    dict(slug="watchy", short="E-cinema", name="Watchy", kicker="E-cinema booking platform", color="pink", ico="ticket",
         regions=[("EG", "Egypt", "pink")],
         desc="A full e-cinema platform where users browse movies, pick showtimes, book seats and manage their cinema tickets end to end.",
         tags=["ASP.NET MVC", "C#", "Entity Framework", "SQL Server", "jQuery"], blobs=[("pink", .1, .2, .5), ("purple", .9, .9, .5)]),
    dict(slug="mindmission", short="E-learning", name="Mind Mission", kicker="E-learning platform", color="green", ico="book",
         regions=[("EG", "Egypt", "pink"), ("SA", "Saudi Arabia", "green")],
         desc="A Udemy-style platform where students browse, purchase and take courses, with full course-management tools for instructors and Power BI analytics.",
         tags=["ASP.NET Web API", "Angular", "SQL Server", "EF Core", "Power BI"], blobs=[("green", .1, .2, .5), ("teal", .9, .9, .5)]),
]

TOOLBOX = [
    ("Backend", "server", "indigo", ["C#", ".NET", "ASP.NET Core", "Web API", "MVC", "ASP.NET Zero", "SignalR", "Node.js"]),
    ("Frontend", "layout", "pink", ["Angular", "TypeScript", "JavaScript", "HTML", "SCSS", "Bootstrap"]),
    ("Data & BI", "database", "green", ["SQL Server", "Entity Framework", "MongoDB", "Redis", "Power BI", "SSRS"]),
    ("CRM & Cloud", "grid", "blue", ["Dynamics 365", "Power Platform", "Azure DevOps"]),
    ("Integrations", "plug", "orange", ["PayFort", "HyperPay", "Apple Pay", "WhatsApp Business API"]),
    ("Practices", "branch", "purple", ["Clean Architecture", "Agile / Scrum", "CI/CD", "Git"]),
]

LINKS = [
    ("portfolio", "Portfolio", "globe", "blue"),
    ("linkedin", "LinkedIn", "linkedin", "indigo"),
    ("email", "Email", "mail", "orange"),
    ("whatsapp", "WhatsApp", "chat", "green"),
]


def compact():
    return W < 700


def panel(d, x, y, w, h, r=18):
    t = d.t
    d.body.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{r}" fill="{t["chip"]}" fill-opacity="{t["chip_o"]}" '
                  f'stroke="{t["chip_stroke"]}" stroke-opacity="{t["chip_stroke_o"]}"/>')


def flow_chips(d, x0, y0, maxx, labels, size=12.5, h=26, pad=11, gap=8, measure_only=False, **kw):
    """Lay chips out left-to-right, wrapping to new rows. Returns the bottom y."""
    x, y = x0, y0
    for lb in labels:
        w = tw(lb, size) + pad * 2 + (14 if kw.get("dot") else 0)
        if x + w > maxx and x > x0:
            x, y = x0, y + h + gap
        if not measure_only:
            d.chip(x, y, lb, size, h, pad, **kw)
        x += w + gap
    return y + h



def with_header(d, title, ico, color, meta=None, badge=None):
    """Re-wrap a card so its section title sits inside the glass, iOS widget style:
    icon tile + title on the left, a meta capsule on the right, hairline divider below."""
    C = compact()
    t = d.t
    pad = 32 if C else 40
    ts = 44 if C else 36
    H = (ts + 40) if C else (ts + 36)
    r, blobs = d.glass_args
    n = Doc(d.w, d.h + H, [k for k, v in THEMES.items() if v is t][0], d.title)
    n.n = 1000  # keep ids unique from the wrapped card
    n.glass(4, 4, d.w - 8, d.h + H - 8, r, blobs)
    y = 26
    n.tile(pad, y, ts, color, ico)
    n.body.append(T(pad + ts + 14, y + ts / 2 + (9 if C else 7.5), title, 25 if C else 20, t["ink"], 740, ls="-.3"))
    if meta:
        size = 15 if C else 13
        w = tw(meta, size) + 26
        n.chip(d.w - pad - w, y + (ts - (32 if C else 28)) / 2, meta, size, 32 if C else 28, 13)
    if badge:
        n.body.append(T(d.w - pad, y + ts / 2 + 6, badge, 15 if C else 13, IOS[color][t["idx"]], 700, "end", ls="1"))
    n.body.append(f'<rect x="{pad}" y="{y + ts + 16}" width="{d.w - pad * 2}" height="1" fill="{t["hair"]}" fill-opacity="{float(t["hair_o"]) + .03:.2f}"/>')
    n.defs += d.defs
    n.body.append(f'<g transform="translate(0 {H - 14})">' + "".join(d.body[1:]) + "</g>")
    return n


def card_header(mode):
    C = compact()
    title = "Abdelrahman Elsayed Ouf — Software Engineer"
    blobs = [("indigo", .08, .1, .45), ("pink", .55, -.1, .35), ("cyan", .95, .95, .45), ("orange", .35, 1.1, .3)]
    chips = [("Open to work", dict(dot="green")), ("Cairo, Egypt", dict(ico="pin")), ("Egypt · Saudi Arabia · UAE", dict(ico="globe"))]
    if not C:
        d = Doc(W, 280, mode, title); t = d.t
        d.glass(4, 4, W - 8, 272, 34, blobs)
        d.tile(44, 52, 112, "indigo", None, "AO")
        d.body.append(T(184, 84, "SOFTWARE ENGINEER", 14, IOS["blue"][t["idx"]], 700, ls="1.6"))
        d.body.append(T(182, 132, "Abdelrahman Elsayed Ouf", 44, t["ink"], 750, ls="-.6"))
        d.body.append(T(184, 166, ".NET  ·  Angular  ·  Dynamics 365  ·  3+ years shipping production platforms", 17, t["ink2"], 500))
        x = 184
        for lb, kw in chips:
            x += d.chip(x, 192, lb, 14, 34, 14, **kw) + 10
        return d
    # compact: stacked, larger relative type
    sub = wrap(".NET · Angular · Dynamics 365 · 3+ years shipping production platforms", 19, W - 80, False)
    y_chips = 236 + len(sub) * 28
    rows_y, x = y_chips, 36
    for lb, kw in chips:
        w = tw(lb, 16) + 32 + (14 if kw.get("dot") else 0) + (22 if kw.get("ico") else 0)
        if x + w > W - 36 and x > 36:
            x, rows_y = 36, rows_y + 48
        x += w + 10
    h = rows_y + 40 + 40
    d = Doc(W, h, mode, title); t = d.t
    d.glass(4, 4, W - 8, h - 8, 34, blobs)
    d.tile(36, 36, 92, "indigo", None, "AO")
    d.body.append(T(38, 166, "SOFTWARE ENGINEER", 15, IOS["blue"][t["idx"]], 700, ls="1.6"))
    d.body.append(T(36, 208, "Abdelrahman Ouf", 40, t["ink"], 760, ls="-.6"))
    y = 244
    for ln in sub:
        d.body.append(T(38, y, ln, 19, t["ink2"], 500))
        y += 28
    x, y = 36, y_chips
    for lb, kw in chips:
        w = tw(lb, 16) + 32 + (14 if kw.get("dot") else 0) + (22 if kw.get("ico") else 0)
        if x + w > W - 36 and x > 36:
            x, y = 36, y + 48
        x += d.chip(x, y, lb, 16, 40, 16, **kw) + 10
    return d


def card_link(mode, key, label, ico, color):
    w = 196
    d = Doc(w, 56, mode, label)
    d.glass(2, 2, w - 4, 52, 26, [(color, .15, .2, .8), ("purple" if color != "purple" else "blue", .95, .9, .6)])
    d.tile(10, 10, 36, color, ico)
    d.body.append(T(58, 34, label, 16, d.t["ink"], 650))
    d.body.append(icon("chevron", w - 34, 19, 18, d.t["ink3"], 2.4))
    return d


def section_label(mode, slug, text, ico, color):
    C = compact()
    s = 52 if C else 40
    d = Doc(W, s + 24, mode, text)
    d.tile(4, 12, s, color, ico)
    d.body.append(T(s + 22, 12 + s / 2 + (11 if C else 9), text, 30 if C else 24, d.t["ink"], 720, ls="-.3"))
    return d


def card_about(mode):
    C = compact()
    t = THEMES[mode]
    para = ("I'm a full-stack software engineer based in Cairo with 3+ years of production experience. "
            "I build efficient backends with ASP.NET Core, dynamic frontends with Angular, and extend business "
            "systems with Microsoft Dynamics 365 — for clients across Egypt, Saudi Arabia and the UAE.")
    facts = [("briefcase", "blue", "Full-Stack .NET Engineer", "Excellent Protection · Jul 2023 — Present"),
             ("award", "orange", "Microsoft Certified", "Power Platform Functional Consultant Associate"),
             ("plug", "green", "Payments & messaging", "PayFort · HyperPay · Apple Pay · WhatsApp API"),
             ("cap", "purple", "Education", "ITI Web & BI Diploma · B.Sc. Petroleum Eng.")]
    metrics = [("3+", "Years experience", "blue"), ("3", "Countries served", "green"),
               ("5+", "Production projects", "orange"), ("1", "Microsoft certification", "purple")]
    pad = 36 if C else 48
    fs, lh = (19, 30) if C else (17, 27)
    lines = wrap(para, fs, W - pad * 2, False)
    fcols, mcols = (1, 2) if C else (2, 4)
    fh, ff, fsub = (84, 18, 15.5) if C else (66, 15.5, 13.5)
    mh = 116 if C else 100
    colw = (W - pad * 2 - 16 * (fcols - 1)) / fcols
    mw = (W - pad * 2 - 16 * (mcols - 1)) / mcols
    frows = (len(facts) + fcols - 1) // fcols
    mrows = (len(metrics) + mcols - 1) // mcols
    top = 48 + 12
    y_f = top + len(lines) * lh + 4
    y_m = y_f + frows * (fh + 12) + 8
    h = y_m + mrows * (mh + 14) + 26
    d = Doc(W, h, mode, "About Abdelrahman")
    d.glass(4, 4, W - 8, h - 8, 34, [("blue", .05, .1, .4), ("purple", .95, .35, .35), ("green", .2, 1.0, .35)])
    y = top
    for ln in lines:
        d.body.append(T(pad, y, ln, fs, t["ink2"], 500)); y += lh
    ts = 52 if C else 44
    for i, (ico, col, title, sub) in enumerate(facts):
        cx = pad + (i % fcols) * (colw + 16)
        cy = y_f + (i // fcols) * (fh + 12)
        panel(d, cx, cy, colw, fh)
        d.tile(cx + 14, cy + (fh - ts) / 2, ts, col, ico)
        tx = cx + 14 + ts + 14
        d.body.append(T(tx, cy + fh / 2 - 4, title, ff, t["ink"], 680))
        sl = wrap(sub, fsub, colw - (tx - cx) - 12, False)
        d.body.append(T(tx, cy + fh / 2 + fsub + 2, sl[0] + ("…" if len(sl) > 1 else ""), fsub, t["ink2"], 500))
    for i, (num, lab, col) in enumerate(metrics):
        mx = pad + (i % mcols) * (mw + 16)
        my = y_m + (i // mcols) * (mh + 14)
        panel(d, mx, my, mw, mh, 22)
        d.body.append(T(mx + 20, my + (62 if C else 54), num, 44 if C else 38, IOS[col][t["idx"]], 760, ls="-1"))
        d.body.append(T(mx + 20, my + (94 if C else 80), lab, 16 if C else 14, t["ink2"], 600))
    return d


def card_project(mode, p):
    C = compact()
    t = THEMES[mode]
    title = f'{p["name"]} — {p["kicker"]}'
    if not C:
        x0 = 164
        lines = wrap(p["desc"], 15.5, W - x0 - 100, False)
        ty = 112 + (len(lines) - 1) * 24 + 22
        h = max(ty + 26 + 38, 176)
        d = Doc(W, h, mode, title)
        d.glass(4, 4, W - 8, h - 8, 30, p["blobs"])
        d.tile(40, 40, 96, p["color"], p["ico"])
        d.body.append(T(x0 - 1, 80, p["name"], 30, t["ink"], 740, ls="-.4"))
        rx = x0 + tw(p["name"], 30) + 18
        for code, name, col in p["regions"]:
            rx += d.chip(rx, 58, name, 12.5, 26, 10, dot=col) + 8
        y = 112
        for ln in lines:
            d.body.append(T(x0, y, ln, 15.5, t["ink2"], 500)); y += 24
        tx = x0
        for tg in p["tags"]:
            w = tw(tg, 12.5) + 22
            if tx + w > W - 60:
                break
            tx += d.chip(tx, ty, tg, 12.5, 26, 11) + 8
        panel(d, W - 70, h / 2 - 18, 36, 36, 18)
        d.body.append(icon("chevron", W - 61, h / 2 - 9, 18, t["ink2"], 2.4))
        return d
    pad = 32
    lines = wrap(p["desc"], 18, W - pad * 2, False)
    y_desc = 168
    y_tags = y_desc + (len(lines) - 1) * 28 + 26
    tmp = Doc(W, 10, mode, "")
    end = flow_chips(tmp, pad, y_tags, W - pad, p["tags"], 15, 32, 13, 8, measure_only=True)
    h = end + 34
    d = Doc(W, h, mode, title)
    d.glass(4, 4, W - 8, h - 8, 30, p["blobs"])
    d.tile(pad, 32, 80, p["color"], p["ico"])
    x0 = pad + 80 + 20
    d.body.append(T(x0 - 1, 66, p["name"], 32, t["ink"], 750, ls="-.4"))
    rx = x0
    for code, name, col in p["regions"]:
        rx += d.chip(rx, 80, name, 14, 30, 12, dot=col) + 8
    y = y_desc
    for ln in lines:
        d.body.append(T(pad, y, ln, 18, t["ink2"], 500)); y += 28
    flow_chips(d, pad, y_tags, W - pad, p["tags"], 15, 32, 13, 8)
    return d


def card_toolbox(mode):
    C = compact()
    t = THEMES[mode]
    cols = 1 if C else 2
    pad = 32 if C else 40
    fs, lh, ts, hs = (16, 24, 48, 18) if C else (13, 20, 40, 15)
    colw = (W - pad * 2 - 16 * (cols - 1)) / cols
    textx = 14 + ts + 14
    layouts = []
    for _, _, _, items in TOOLBOX:
        # wrap by whole items so a tool name never splits across lines
        lines, cur = [], ""
        for it in items:
            nxt = (cur + "  ·  " + it) if cur else it
            if tw(nxt, fs, False) > colw - textx - 14 and cur:
                lines.append(cur); cur = it
            else:
                cur = nxt
        lines.append(cur)
        layouts.append(lines)
    groups = [layouts[i:i + cols] for i in range(0, len(layouts), cols)]
    rowhs = [(ts + 8 if C else 44) + (max(len(l) for l in g) - (1 if C else 0)) * lh + (16 if C else 0) for g in groups]
    rowhs = [max(r, ts + 24) for r in rowhs]
    top = 30
    h = top * 2 + sum(rowhs) + 12 * (len(rowhs) - 1)
    d = Doc(W, h, mode, "Toolbox")
    d.glass(4, 4, W - 8, h - 8, 34, [("indigo", .05, .1, .4), ("pink", .6, 1.0, .35), ("cyan", 1.0, .1, .35)])
    for i, (name, ico, col, items) in enumerate(TOOLBOX):
        r = i // cols
        rowh = rowhs[r]
        cx = pad + (i % cols) * (colw + 16)
        cy = top + sum(rowhs[:r]) + 12 * r
        panel(d, cx, cy, colw, rowh, 20)
        d.tile(cx + 14, cy + 12, ts, col, ico)
        d.body.append(T(cx + textx, cy + 12 + hs + 4, name, hs, t["ink"], 700))
        for j, ln in enumerate(layouts[i]):
            d.body.append(T(cx + textx, cy + 12 + hs + 8 + (j + 1) * lh - 4, ln, fs, t["ink2"], 500))
    return d


def card_footer(mode):
    C = compact()
    t = THEMES[mode]
    if not C:
        d = Doc(W, 150, mode, "Let's build something together")
        d.glass(4, 4, W - 8, 142, 32, [("purple", .1, .1, .45), ("blue", .9, .9, .45)])
        d.tile(40, 39, 72, "purple", "sparkles")
        d.body.append(T(136, 70, "Let's build something together", 26, t["ink"], 740, ls="-.3"))
        d.body.append(T(136, 102, "Open to full-time roles and freelance work · abd-elrahman_elsayed@outlook.com", 15.5, t["ink2"], 500))
        return d
    d = Doc(W, 236, mode, "Let's build something together")
    d.glass(4, 4, W - 8, 228, 32, [("purple", .1, .1, .45), ("blue", .9, .9, .45)])
    d.tile(32, 32, 64, "purple", "sparkles")
    d.body.append(T(32, 140, "Let's build together", 30, t["ink"], 750, ls="-.3"))
    d.body.append(T(32, 174, "Open to full-time roles and freelance work", 17, t["ink2"], 500))
    d.body.append(T(32, 202, "abd-elrahman_elsayed@outlook.com", 17, IOS["blue"][t["idx"]], 650))
    return d



# ───────────────────── tiled sections (each tile = its own link) ─────────────────────
SECTION_GAP = 14      # transparent space above/below each full-width section
TILE_GAP = 2          # transparent space above/below tiles inside a section

LINK_TILES = [
    ("portfolio", "Portfolio", "Browse my work", "globe", "blue"),
    ("linkedin", "LinkedIn", "in/abdelrahman-ouf", "linkedin", "indigo"),
    ("email", "Email", "Say hello", "mail", "orange"),
    ("whatsapp", "WhatsApp", "+20 100 689 2802", "chat", "green"),
]


def spaced(d, top=SECTION_GAP, bottom=SECTION_GAP):
    d.mt, d.mb = top, bottom
    return d


def hline(d, x, y, w):
    t = d.t
    d.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="{t["hair"]}" fill-opacity="{float(t["hair_o"]) + .04:.2f}"/>')


def vline(d, x, y, h):
    t = d.t
    d.body.append(f'<rect x="{x}" y="{y}" width="1" height="{h}" fill="{t["hair"]}" fill-opacity="{float(t["hair_o"]) + .04:.2f}"/>')


def panel_links(mode):
    """One wide glass panel holding all four links; sliced into 4 clickable columns."""
    C = compact()
    PW = 1000
    G = SECTION_GAP
    inner = 120 if C else 76
    H = G + 4 + inner + 4 + G
    d = Doc(PW, H, mode, "Links")
    t = d.t
    d.glass(4, G + 4, PW - 8, inner, 30 if C else 26, [("blue", .05, .3, .3), ("indigo", .35, 1.0, .3), ("orange", .65, 0, .3), ("green", .95, .8, .3)])
    cw = PW / 4
    top = G + 4
    ts, fs, gap = (50, 25, 10) if C else (40, 19, 12)
    for i, (key, label, sub, ico, col) in enumerate(LINK_TILES):
        cx = i * cw
        if i:
            vline(d, cx - 1, top + inner * .25, inner * .5)
        group = ts + gap + tw(label, fs)
        gx = cx + (cw - group) / 2
        d.tile(gx, top + (inner - ts) / 2, ts, col, ico)
        d.body.append(T(gx + ts + gap, top + inner / 2 + fs * .36, label, fs, t["ink"], 700, ls="-.2"))
    slices = [(i * cw, 0, cw, H, LINK_TILES[i][1]) for i in range(4)]
    return d, slices


def draw_project(d, ox, oy, w, h, p, C):
    t = d.t
    pad = 34 if C else 30
    if C:
        ts, name_fs, kick_fs, reg_fs, reg_h, tag_fs, tag_h = 108, 38, 28, 26, 52, 26, 52
        tags, desc = p["tags"][:3], []
    else:
        ts, name_fs, kick_fs, reg_fs, reg_h, tag_fs, tag_h = 64, 26, 12.5, 12.5, 28, 13, 28
        tags, desc = p["tags"], wrap(p["desc"], 15.5, w - pad * 2 - 16, False)
    x0, y0 = ox + pad, oy + pad
    d.tile(x0, y0, ts, p["color"], p["ico"])
    tx = x0 + ts + (22 if C else 18)
    d.body.append(T(tx, y0 + ts / 2 - (8 if C else 4), p["name"], name_fs, t["ink"], 750, ls="-.4"))
    d.body.append(T(tx, y0 + ts / 2 + (34 if C else 18), p["short"] if C else p["kicker"], kick_fs, IOS[p["color"]][t["idx"]], 650))
    if not C:
        panel(d, ox + w - pad - 34, y0, 34, 34, 17)
        d.body.append(icon("chevron", ox + w - pad - 26, y0 + 8, 18, t["ink2"], 2.4))
    y = y0 + ts + 22
    x = x0
    for code, name, col in p["regions"]:
        x += d.chip(x, y, name, reg_fs, reg_h, 18 if C else 10, dot=col) + 10
    y += reg_h + 30
    for ln in desc:
        d.body.append(T(x0, y, ln, 15.5, t["ink2"], 500)); y += 24
    tmp = Doc(10, 10, "light", "")
    block = flow_chips(tmp, 0, 0, w - pad * 2, tags, tag_fs, tag_h, 20 if C else 11, 10 if C else 8, measure_only=True)
    flow_chips(d, x0, oy + h - pad - block, ox + w - pad, tags, tag_fs, tag_h, 20 if C else 11, 10 if C else 8)


def project_need(p, C, w):
    pad = 34 if C else 30
    if C:
        ts, reg_h, tag_fs, tag_h, tags, desc = 108, 52, 26, 52, p["tags"][:3], []
    else:
        ts, reg_h, tag_fs, tag_h, tags, desc = 64, 28, 13, 28, p["tags"], wrap(p["desc"], 15.5, w - pad * 2 - 16, False)
    tmp = Doc(10, 10, "light", "")
    block = flow_chips(tmp, 0, 0, w - pad * 2, tags, tag_fs, tag_h, 20 if C else 11, 10 if C else 8, measure_only=True)
    body = ts + 22 + reg_h + 30 + (len(desc) * 24 - 6 if desc else -12)
    return pad + body + 16 + block + pad


def panel_projects(mode):
    """Header strip + 2×2 grid inside ONE glass panel; sliced into a header and four clickable cells."""
    C = compact()
    PW, G = 1000, SECTION_GAP
    cw = PW / 2
    hdr = 150 if C else 96
    ch = max(project_need(p, C, cw) for p in PROJECTS)
    H = G + 4 + hdr + 2 * ch + 4 + G
    d = Doc(PW, H, mode, "Featured projects")
    t = d.t
    d.glass(4, G + 4, PW - 8, H - 2 * G - 8, 32,
            [("indigo", .05, .2, .3), ("orange", .95, .25, .3), ("green", .05, .85, .3), ("blue", .95, .9, .3)])
    top = G + 4
    pad = 34 if C else 30
    ts = 72 if C else 44
    d.tile(pad, top + (hdr - ts) / 2, ts, "blue", "layers")
    tx = pad + ts + 18
    d.body.append(T(tx, top + hdr / 2 - (4 if C else 2), "Featured projects", 44 if C else 22, t["ink"], 740, ls="-.4"))
    d.body.append(T(tx, top + hdr / 2 + (36 if C else 20), "Tap a card to open it" if C else "Production platforms · click a card to open its repository", 26 if C else 14, t["ink2"], 500))
    meta = "4 featured projects"
    msz = 22 if C else 13
    mh = 46 if C else 28
    if not C:
        mw = tw(meta, msz) + 26
        d.chip(PW - pad - mw, top + (hdr - mh) / 2, meta, msz, mh, 13)
    gy = top + hdr
    hline(d, pad, gy - 1, PW - pad * 2)
    vline(d, cw - 1, gy + 24, 2 * ch - 48)
    hline(d, pad, gy + ch - 1, PW - pad * 2)
    for i, p in enumerate(PROJECTS):
        draw_project(d, (i % 2) * cw, gy + (i // 2) * ch, cw, ch, p, C)
    slices = [(0, 0, PW, gy, "Featured projects")]
    for i, p in enumerate(PROJECTS):
        h = ch + (4 + G if i >= 2 else 0)
        slices.append(((i % 2) * cw, gy + (i // 2) * ch, cw, h, f'{p["name"]} — {p["kicker"]}'))
    return d, slices


# ──────────────────────────────── stats ────────────────────────────────
LANG_COLORS = ["blue", "purple", "orange", "green", "pink", "teal"]


def gh(query, token):
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    q = """query { user(login: "%s") {
      followers { totalCount }
      contributionsCollection { contributionCalendar { totalContributions } totalPullRequestContributions }
      repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
        totalCount
        nodes { stargazerCount languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
      } } }""" % USER
    u = gh(q, token)["data"]["user"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    return dict(
        contributions=u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        prs=u["contributionsCollection"]["totalPullRequestContributions"],
        repos=u["repositories"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        followers=u["followers"]["totalCount"],
        langs=[(n, s / total) for n, s in top],
    )


def card_stats(mode, s):
    C = compact()
    t = THEMES[mode]
    pad = 32 if C else 40
    cols = 2 if C else 4
    mh = 120 if C else 96
    mw = (W - pad * 2 - 16 * (cols - 1)) / cols
    fmt = (lambda k: f"{s[k]:,}") if s else (lambda k: "—")
    metrics = [("activity", "blue", fmt("contributions"), "Contributions · last year" if not C else "Contributions (year)"),
               ("folder", "green", fmt("repos"), "Public repositories" if not C else "Public repos"),
               ("star", "orange", fmt("stars"), "Stars earned"),
               ("users", "purple", fmt("followers"), "Followers")]
    langs = s["langs"] if s else []
    ls_, lfs = (16, 15) if C else (13.5, 13.5)
    # measure legend rows
    leg, x, y = [], pad, 0
    for i, (name, frac) in enumerate(langs):
        label = f"{name} {frac * 100:.0f}%"
        w = tw(label, lfs) + 40
        if x + w > W - pad and x > pad:
            x, y = pad, y + 26
        leg.append((x, y, label, i)); x += w
    mrows = (4 + cols - 1) // cols
    y_lang = 36 + mrows * (mh + 14) + 18
    h = y_lang + 14 + 12 + 26 + (y if langs else 0) + 30
    d = Doc(W, h, mode, "GitHub activity")
    d.glass(4, 4, W - 8, h - 8, 34, [("blue", .05, .1, .4), ("green", .95, .2, .35), ("orange", .5, 1.1, .3)])
    ts = 44 if C else 36
    for i, (ico, col, val, lab) in enumerate(metrics):
        mx = pad + (i % cols) * (mw + 16)
        my = 36 + (i // cols) * (mh + 14)
        panel(d, mx, my, mw, mh, 22)
        d.tile(mx + 16, my + 16, ts, col, ico)
        d.body.append(T(mx + 16 + ts + 12, my + 16 + ts / 2 + (11 if C else 9), val, 32 if C else 26, t["ink"], 750, ls="-.5"))
        d.body.append(T(mx + 16, my + mh - (22 if C else 16), lab, 16 if C else 13, t["ink2"], 600))
    d.body.append(T(pad, y_lang, "Top languages", 18 if C else 15, t["ink"], 700))
    bx, by, bw, bh = pad, y_lang + 14, W - pad * 2, 12
    cid = d.uid("bar")
    d.defs.append(f'<clipPath id="{cid}"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6"/></clipPath>')
    seg = [f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{t["chip"]}" fill-opacity="{t["chip_o"]}"/>']
    x = bx
    for i, (name, frac) in enumerate(langs):
        w = bw * frac
        seg.append(f'<rect x="{x:.1f}" y="{by}" width="{w + .5:.1f}" height="{bh}" fill="{IOS[LANG_COLORS[i]][t["idx"]]}"/>')
        x += w
    d.body.append(f'<g clip-path="url(#{cid})">{"".join(seg)}</g>')
    base = by + bh + 26
    if langs:
        for lx, ly, label, i in leg:
            d.body.append(f'<circle cx="{lx + 5}" cy="{base + ly - 5}" r="5" fill="{IOS[LANG_COLORS[i]][t["idx"]]}"/>')
            d.body.append(T(lx + 16, base + ly, label, lfs, t["ink2"], 600))
    else:
        d.body.append(T(pad, base, "Refreshes daily via GitHub Actions." if C else "Stats refresh automatically every day via GitHub Actions.", lfs, t["ink2"], 500))
    return d


# ──────────────────────────────── build ────────────────────────────────

def save(name, doc):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc.render())


SIZES = [("", 1000), ("-m", 600)]   # wide (desktop) and compact (phones) variants


def main():
    global W
    os.makedirs(OUT, exist_ok=True)
    stats_only = "--stats" in sys.argv
    s = None
    if stats_only or os.environ.get("GITHUB_TOKEN"):
        try:
            s = fetch_stats()
        except Exception as e:  # never wipe good stats because of an API hiccup
            print("stats fetch failed:", e)
            if stats_only:
                sys.exit(0)
    for suffix, width in SIZES:
        W = width
        for mode in THEMES:
            save(f"stats{suffix}-{mode}.svg", spaced(with_header(card_stats(mode, s), "GitHub activity", "activity", "green", "Updated daily")))
            if stats_only:
                continue
            C = width < 700
            save(f"header{suffix}-{mode}.svg", spaced(card_header(mode), 0, SECTION_GAP))
            save(f"about{suffix}-{mode}.svg", spaced(with_header(card_about(mode), "About me", "sparkles", "purple", "Cairo · Since 2023")))
            save(f"toolbox{suffix}-{mode}.svg", spaced(with_header(card_toolbox(mode), "Toolbox", "code", "pink", "6 areas" if C else "6 areas · 30+ tools")))
            save(f"footer{suffix}-{mode}.svg", spaced(card_footer(mode), SECTION_GAP, 0))
            for prefix, builder, names in [("link", panel_links, [k for k, *_ in LINK_TILES]),
                                           ("project", panel_projects, ["head"] + [p["slug"] for p in PROJECTS])]:
                pd, slices = builder(mode)
                for name, (x, y, w, h, title) in zip(names, slices):
                    with open(os.path.join(OUT, f"{prefix}-{name}{suffix}-{mode}.svg"), "w", encoding="utf-8") as f:
                        f.write(pd.render_slice(x, y, w, h, title))
    print("built", len(os.listdir(OUT)), "files", "(stats live)" if s else "(stats placeholder)")


if __name__ == "__main__":
    main()
