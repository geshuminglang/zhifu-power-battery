#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZHIFU Technology — static H5 product catalogue generator.

Run:  python build.py
Output: all HTML pages in this folder (index.html, products.html, ... products/*.html)

Everything is plain static HTML/CSS/JS: no server, no build tools, no database.
Upload the whole folder to any host (Netlify, Vercel, Cloudflare Pages, GitHub
Pages, Alibaba Cloud OSS, Tencent COS, nginx/Apache, ...) and it works.

--------------------------------------------------------------------------
>>> EDIT THE VALUES IN THE "SITE CONFIG" BLOCK BELOW, THEN RUN build.py <<<
--------------------------------------------------------------------------
"""

import os
import json
import html
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# =========================================================================
# SITE CONFIG — change these to your real details
# =========================================================================
SITE_URL = "https://www.wenrey-battery.com"      # replace with the final public domain before launch
BRAND = "ZHIFU"
BRAND_SUB = "Power Your Journey"
COMPANY = "Guangdong Zhifu Technology Co., Ltd."
COMPANY_CN = "广东志富科技有限公司"
EMAIL = "yizong2023@outlook.com"
PHONE = "+86 15826560159"
WHATSAPP = "+86 15826560159"                       # display format; the link is normalised below
WECHAT = "zhifu-sales"
ADDRESS = "Huiyang District, Huizhou, Guangdong, China"
ADDRESS_CN = "中国广东省惠州市惠阳区"
LEGAL_NOTE = ""                                    # e.g. "ICP备xxxxxxxx号" once you host in mainland China

STATS = [
    ("15+", "Years in energy storage batteries"),
    ("100+", "Countries served"),
    ("5,000 m²", "Manufacturing area"),
    ("100+", "Employees"),
]

CERTIFICATIONS = ["CE", "CB", "CCC", "FC", "MSDS", "UN38.3"]

# =========================================================================
# PRODUCT DATA (taken from the printed English product manual)
# =========================================================================
MIN_CAP = "\u2265 98% of rated capacity"
INTERNAL_R = "\u2264 0.47 m\u03a9"
SELF_DISCHARGE = "\u2264 50 \u00b5A"
CHARGE_MODE = "CC&CV (constant current and constant voltage)"

APPLICATIONS = {
    "30": ["Electric motorcycle", "Electric scooter", "E-bike & light EV"],
    "67": ["Electric motorcycle", "Electric tricycle", "Low-speed electric vehicle"],
    "120": ["Electric tricycle", "Low-speed electric vehicle", "Golf cart & sightseeing car"],
    "166": ["Electric tricycle", "Low-speed electric vehicle", "Golf cart & sightseeing car", "Energy storage"],
}

PRODUCTS = [
    dict(slug="72v-30ah",  model="72V 30Ah",  voltage=72, capacity=30,  energy=2304,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=10, max_chg=15, max_dis=60,  peak=120, ship="78 V \u2013 82 V"),
    dict(slug="60v-30ah",  model="60V 30Ah",  voltage=60, capacity=30,  energy=1920,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=10, max_chg=15, max_dis=60,  peak=60,  ship="68 V \u2013 72 V"),
    dict(slug="72v-60ah",  model="72V 60Ah",  voltage=72, capacity=60,  energy=4608,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=20, max_chg=30, max_dis=80,  peak=160, ship="78 V \u2013 82 V"),
    dict(slug="60v-60ah",  model="60V 60Ah",  voltage=60, capacity=60,  energy=3840,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=20, max_chg=30, max_dis=80,  peak=160, ship="68 V \u2013 72 V"),
    dict(slug="72v-67ah",  model="72V 67Ah",  voltage=72, capacity=67,  energy=5145,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=20, max_chg=30, max_dis=80,  peak=160, ship="78 V \u2013 82 V"),
    dict(slug="60v-67ah",  model="60V 67Ah",  voltage=60, capacity=67,  energy=4288,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=20, max_chg=30, max_dis=80,  peak=160, ship="68 V \u2013 72 V"),
    dict(slug="72v-100ah", model="72V 100Ah", voltage=72, capacity=100, energy=7680,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=20, max_chg=40, max_dis=120, peak=240, ship="78 V \u2013 82 V"),
    dict(slug="60v-100ah", model="60V 100Ah", voltage=60, capacity=100, energy=6400,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=20, max_chg=40, max_dis=150, peak=240, ship="68 V \u2013 72 V"),
    dict(slug="72v-120ah", model="72V 120Ah", voltage=72, capacity=120, energy=9216,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=20, max_chg=40, max_dis=150, peak=300, ship="78 V \u2013 82 V"),
    dict(slug="60v-120ah", model="60V 120Ah", voltage=60, capacity=120, energy=7680,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=20, max_chg=40, max_dis=150, peak=300, ship="68 V \u2013 72 V"),
    dict(slug="72v-166ah", model="72V 166Ah", voltage=72, capacity=166, energy=12748,
         rated_v=76.8, chg_cut=87.6, dis_cut=60, std_chg=20, max_chg=40, max_dis=200, peak=400, ship="78 V \u2013 82 V"),
    dict(slug="60v-166ah", model="60V 166Ah", voltage=60, capacity=166, energy=10624,
         rated_v=64,   chg_cut=73,   dis_cut=50, std_chg=20, max_chg=40, max_dis=200, peak=400, ship="68 V \u2013 72 V"),
]


def app_key_for(capacity):
    if capacity <= 30:
        return "30"
    if capacity <= 67:
        return "67"
    if capacity <= 120:
        return "120"
    return "166"


for p in PRODUCTS:
    p["applications"] = APPLICATIONS[app_key_for(p["capacity"])]
    p["tier"] = {72: "High-voltage", 60: "Standard-voltage"}[p["voltage"]]


HIGHLIGHTS = [
    "High-performance lithium-ion cells, capacity-matched and sorted before assembly",
    "Integrated BMS: over-charge, over-discharge, over-current and short-circuit protection",
    "CC&CV charging with a wide operating voltage window",
    "UN38.3 and MSDS compliant \u2014 safe for air and sea transport",
    "OEM / ODM: custom housing, connector, communication protocol and branding",
]

# =========================================================================
# Small helpers
# =========================================================================
WA_NUMBER = WHATSAPP.replace("+", "").replace(" ", "")


def e(text):
    return html.escape(str(text), quote=True)


ICONS = {
    "bolt": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "factory": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20h20"/><path d="M4 20V9l5 3V9l5 3V4l4 3v13"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1.5"/><circle cx="18" cy="21" r="1.5"/><path d="M1 2h3l3 13h12l3-9H6"/></svg>',
    "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.7" y2="16.7"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8z"/></svg>',
    "qr": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM21 14v3M14 21h7"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
}


def icon(name):
    return ICONS.get(name, "")


def rel(depth, path=""):
    """Relative URL from a page at `depth` levels below the site root."""
    return ("../" * depth) + path


def nav_html(depth, active):
    items = [
        ("index.html", "Home", "home"),
        ("products.html", "Products", "products"),
        ("applications.html", "Applications", "applications"),
        ("about.html", "About", "about"),
        ("contact.html", "Contact", "contact"),
    ]
    out = []
    for href, label, key in items:
        cls = ' class="is-active"' if key == active else ""
        out.append('<a href="%s"%s>%s</a>' % (rel(depth, href), cls, e(label)))
    return "\n        ".join(out)


def header_html(depth, active):
    return """<header class="site-header" id="siteHeader">
  <div class="container header-inner">
    <a class="brand" href="{home}">
      <img class="brand__logo" src="{logo}" alt="{brand}" width="1580" height="449">
    </a>
    <nav class="nav" id="primaryNav" aria-label="Main navigation">
        {nav}
    </nav>
    <div class="header-actions">
      <a class="btn btn--sm header-cta" href="{contact}">Get a quote</a>
      <button class="nav-toggle" id="navToggle" type="button" aria-label="Toggle navigation" aria-expanded="false" aria-controls="primaryNav"><span></span></button>
    </div>
  </div>
</header>""".format(home=rel(depth, "index.html"), brand=e(BRAND),
                   logo=rel(depth, "assets/img/logo-primary.svg.png"),
                   nav=nav_html(depth, active), contact=rel(depth, "contact.html"))


def footer_html(depth):
    cat_links = "\n".join(
        '<li><a href="%s">%s</a></li>' % (rel(depth, "products/" + p["slug"] + ".html"), e(p["model"]))
        for p in PRODUCTS[:6]
    )
    certs = " ".join('<li class="cert">%s</li>' % e(c) for c in CERTIFICATIONS)
    return """<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a class="brand" href="{home}">
          <img class="brand__mark-img" src="{logo}" alt="" width="776" height="776">
          <span class="brand__text">
            <span class="brand__name">{brand}</span>
            <span class="brand__sub">{sub}</span>
          </span>
        </a>
        <p class="footer-about">{company} &mdash; {tagline}</p>
        <ul class="trust__list" style="margin-top:18px">{certs}</ul>
      </div>
      <div>
        <h4>Products</h4>
        <ul>{cat_links}</ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="{about}">About us</a></li>
          <li><a href="{apps}">Applications</a></li>
          <li><a href="{products}">All products</a></li>
          <li><a href="{contact}">Contact &amp; quotation</a></li>
          <li><a href="{manual}">Full product manual (PDF)</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li><a href="mailto:{email}">{email}</a></li>
          <li><a href="tel:{phone_tel}">{phone}</a></li>
          <li><a href="{wa}" target="_blank" rel="noopener">WhatsApp: {whatsapp}</a></li>
          <li>{address}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> {company} All rights reserved.</span>
      <span>{legal}</span>
    </div>
  </div>
</footer>""".format(
        home=rel(depth, "index.html"), brand=e(BRAND), sub=e(BRAND_SUB),
        logo=rel(depth, "assets/img/logo-white.svg.png"),
        company=e(COMPANY),
        tagline="power batteries and energy storage solutions engineered for the global market.",
        certs=certs, cat_links=cat_links,
        about=rel(depth, "about.html"), apps=rel(depth, "applications.html"),
        products=rel(depth, "products.html"), contact=rel(depth, "contact.html"),
        manual=rel(depth, "assets/docs/wenrey-product-manual.pdf"),
        email=e(EMAIL), phone=e(PHONE), phone_tel=e(PHONE.replace(" ", "")),
        wa="https://wa.me/" + WA_NUMBER, whatsapp=e(WHATSAPP),
        address=e(ADDRESS), legal=e(LEGAL_NOTE))


def head_html(depth, title, description, canonical, extra_head="", og_image=""):
    img = og_image or (SITE_URL + "/assets/img/building.png")
    return """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0b1f4b">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{brand} Technology">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{favicon}" type="image/png">
<link rel="apple-touch-icon" href="{favicon}">
<link rel="stylesheet" href="{css}">
{extra}""".format(
        title=e(title), desc=e(description), canonical=e(canonical), brand=e(BRAND),
        img=e(img), favicon=rel(depth, "assets/img/logo-mark.svg.png"),
        css=rel(depth, "assets/css/style.css"), extra=extra_head)


def scripts_html(depth):
    return """<script>window.ZHIFU = {cfg};</script>
<script src="{qr}" defer></script>
<script src="{js}" defer></script>""".format(
        cfg=json.dumps({
            "siteUrl": SITE_URL,
            "email": EMAIL,
            "phone": PHONE,
            "whatsapp": WHATSAPP,
            "whatsappUrl": "https://wa.me/" + WA_NUMBER,
        }, ensure_ascii=False),
        qr=rel(depth, "assets/js/qrcode-lite.js"),
        js=rel(depth, "assets/js/site.js"))


def page(depth, title, description, canonical_path, body, active, extra_head="", jsonld=None, og_image=""):
    canonical = SITE_URL.rstrip("/") + "/" + canonical_path.lstrip("/")
    ld = ""
    if jsonld:
        blocks = jsonld if isinstance(jsonld, list) else [jsonld]
        for b in blocks:
            ld += '\n<script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False)
    return """<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header}
<main id="main">
{body}
</main>
{footer}
{scripts}
</body>
</html>
""".format(
        head=head_html(depth, title, description, canonical, extra_head + ld, og_image),
        header=header_html(depth, active),
        body=body,
        footer=footer_html(depth),
        scripts=scripts_html(depth))


# =========================================================================
# Reusable blocks
# =========================================================================
def product_card(p, depth, badge=None):
    specs = "<li>%s V</li><li>%d Ah</li><li>%s Wh</li>" % (
        p["voltage"], p["capacity"], format(p["energy"], ","))
    b = badge or ("High voltage" if p["voltage"] == 72 else "Standard voltage")
    return """          <article class="card product-item" data-voltage="{voltage}" data-capacity="{capacity}"
                   data-keywords="{kw}">
            <div class="card__media">
              <span class="badge">{badge}</span>
              <a href="{href}" aria-label="{model} specifications">
                <img src="{img}" alt="{model} lithium-ion battery pack for electric vehicles" loading="lazy" width="1400" height="1070">
              </a>
            </div>
            <div class="card__body">
              <h3 class="card__title"><a href="{href}">{model}</a></h3>
              <p class="card__model">{energy} Wh &middot; {tier}</p>
              <ul class="card__specs">{specs}</ul>
              <div class="card__foot">
                <a class="card__link" href="{href}">View specifications</a>
              </div>
            </div>
          </article>""".format(
        voltage=p["voltage"], capacity=p["capacity"],
        kw=e((p["model"] + " " + str(p["voltage"]) + "v " + str(p["capacity"]) + "ah " +
              " ".join(p["applications"])).lower()),
        badge=e(b), href=rel(depth, "products/" + p["slug"] + ".html"),
        img=rel(depth, "assets/img/product-" + p["slug"] + ".jpg"),
        model=e(p["model"]), energy=format(p["energy"], ","), tier=e(p["tier"]), specs=specs)


def spec_table(p):
    rows = [
        ("Model", p["model"]),
        ("Rated energy", "%s Wh" % format(p["energy"], ",")),
        ("Rated capacity", "%d Ah" % p["capacity"]),
        ("Minimum capacity", MIN_CAP),
        ("Rated voltage", "%.1f V" % p["rated_v"]),
        ("Battery cell internal resistance", INTERNAL_R),
        ("Charging cut-off voltage", "%.1f V" % p["chg_cut"]),
        ("Discharge cut-off voltage", "%g V" % p["dis_cut"]),
        ("Self-consumption", SELF_DISCHARGE),
        ("Charging mode", CHARGE_MODE),
        ("Standard charging current", "%d A" % p["std_chg"]),
        ("Maximum continuous charging current", "%d A" % p["max_chg"]),
        ("Maximum continuous discharge current", "%d A" % p["max_dis"]),
        ("Maximum supported series voltage", "/"),
        ("Maximum supported parallel capacity", "/"),
        ("Peak current (lasts for 2 seconds)", "%d A" % p["peak"]),
        ("Shipping voltage", p["ship"]),
    ]
    body = "\n".join(
        '<tr><th scope="row">%s</th><td>%s</td></tr>' % (e(k), e(v)) for k, v in rows)
    return """<div class="table-wrap">
      <table class="spec">
        <caption>%s &mdash; technical specifications</caption>
        <thead><tr><th scope="col">Project</th><th scope="col">Specifications</th></tr></thead>
        <tbody>
%s
        </tbody>
      </table>
    </div>""" % (e(p["model"]), body)


def cta_band(depth, title, text, product=None):
    q = "contact.html"
    if product:
        q += "?model=" + product["model"].replace(" ", "+")
    return """<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>{title}</h2>
      <p>{text}</p>
      <div class="btn-group">
        <a class="btn btn--light" href="{quote}">Request a quotation</a>
        <a class="btn btn--ghost" href="{wa}" target="_blank" rel="noopener">Chat on WhatsApp</a>
      </div>
    </div>
  </div>
</section>""".format(title=e(title), text=e(text), quote=rel(depth, q),
                    wa="https://wa.me/" + WA_NUMBER)


ORG_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": COMPANY,
    "alternateName": BRAND + " Technology",
    "url": SITE_URL,
    "logo": SITE_URL + "/assets/img/logo-mark.svg.png",
    "email": EMAIL,
    "telephone": PHONE,
    "address": {"@type": "PostalAddress", "addressLocality": "Huizhou",
                "addressRegion": "Guangdong", "addressCountry": "CN",
                "streetAddress": ADDRESS},
    "description": ("Manufacturer of lithium-ion power batteries and energy storage "
                    "solutions for electric motorcycles, tricycles, low-speed EVs, golf "
                    "cars and household / commercial energy storage."),
}


def breadcrumb_jsonld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": SITE_URL.rstrip("/") + "/" + u.lstrip("/")}
            for i, (n, u) in enumerate(items)
        ],
    }


def page_hero(title, text, depth):
    return """<section class="page-hero">
  <div class="container">
    <h1>{title}</h1>
    <p>{text}</p>
  </div>
</section>""".format(title=e(title), text=e(text))


# =========================================================================
# Pages
# =========================================================================
def build_index():
    featured = PRODUCTS[:6]
    cards = "\n".join(product_card(p, 0) for p in featured)
    stats = "\n".join(
        '<div><dt>%s</dt><dd>%s</dd></div>' % (e(v), e(l)) for v, l in STATS)
    certs = "\n".join('<li class="cert">%s</li>' % e(c) for c in CERTIFICATIONS)

    features = [
        ("factory", "Own manufacturing base",
         "5,000 m\u00b2 factory in Huizhou, Guangdong with in-house assembly, testing and quality control."),
        ("shield", "Tested and certified",
         "CE, CB, CCC, FC, MSDS and UN38.3 \u2014 ready for export markets and safe air / sea shipping."),
        ("layers", "Full size range",
         "60 V and 72 V packs from 30 Ah to 166 Ah, so one supplier covers scooters through to storage."),
        ("globe", "Export experience",
         "Projects delivered in more than 100 countries, with export documentation handled end to end."),
    ]
    feat_html = "\n".join("""          <div class="feature">
            <div class="feature__icon">{icon}</div>
            <h3>{t}</h3>
            <p>{d}</p>
          </div>""".format(icon=icon(ic), t=e(t), d=e(d)) for ic, t, d in features)

    apps = [
        ("home", "Household energy storage", "5 kW / 10 kW / 15 kW lithium solutions \u2014 a clean replacement for lead-acid systems."),
        ("truck", "Special vehicle batteries", "Golf cars, sightseeing cars, electric motorcycles, tricycles, quadricycles and recreational vehicles."),
        ("factory", "Commercial &amp; industrial storage", "Scalable battery systems built for energy reliability in commercial and industrial sites."),
        ("sun", "Solar storage integration", "Batteries designed to integrate with renewable energy systems."),
        ("layers", "Customised solutions", "OEM / ODM designs that match your exact housing, connector and communication needs."),
    ]
    apps_html = "\n".join("""          <div class="app-tile">
            <div class="app-tile__icon">{icon}</div>
            <div><h3>{t}</h3><p>{d}</p></div>
          </div>""".format(icon=icon(ic), t=t, d=e(d)) for ic, t, d in apps)

    body = """<section class="hero">
  <div class="hero__bg">
    <img src="assets/img/building.png" alt="ZHIFU Technology headquarters building in Huizhou, Guangdong" width="1448" height="1086">
  </div>
  <div class="container">
    <div class="hero__inner">
      <p class="eyebrow">Lithium battery manufacturer &middot; Huizhou, China</p>
      <h1>Lithium power for <span class="grad">electric mobility</span> and energy storage</h1>
      <p class="hero__lead">ZHIFU builds 60 V and 72 V lithium-ion battery packs from 30 Ah to
        166 Ah for electric motorcycles, tricycles, low-speed vehicles, golf cars and storage
        systems. Browse the complete range online &mdash; no download required.</p>
      <div class="btn-group">
        <a class="btn" href="products.html">Browse products</a>
        <a class="btn btn--ghost" href="contact.html">Request a quotation</a>
      </div>
      <dl class="hero__stats">
{stats}
      </dl>
    </div>
  </div>
</section>

<section class="trust">
  <div class="container trust__inner">
    <span class="trust__label">Certified</span>
    <ul class="trust__list">
{certs}
    </ul>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Core products</p>
      <h2>Battery packs ready for your application</h2>
      <p class="lead">Twelve standard models across two voltage platforms. Every pack ships with
        matched cells, an integrated BMS and full export documentation.</p>
    </div>
    <div class="grid grid--3">
{cards}
    </div>
    <div class="center" style="margin-top:34px">
      <a class="btn btn--outline" href="products.html">See all 12 models</a>
    </div>
  </div>
</section>

<section class="section section--tint">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Shop by platform</p>
      <h2>Choose your voltage platform</h2>
      <p class="lead">The two families share the same design language and BMS architecture, so you
        can standardise across several vehicle platforms.</p>
    </div>
    <div class="grid grid--2">
      <a class="cat-card" href="products.html#v72">
        <img src="assets/img/product-72v-100ah.jpg" alt="72 V lithium battery range" loading="lazy">
        <div class="cat-card__body">
          <p class="tagline">72 V platform</p>
          <h3>72 V &mdash; 30, 60, 67, 100, 120, 166 Ah</h3>
          <p>Rated 76.8 V with 60 V discharge cut-off. Suited to high-speed motorcycles,
            heavy tricycles and larger storage banks.</p>
          <span class="card__link">View 72 V models</span>
        </div>
      </a>
      <a class="cat-card" href="products.html#v60">
        <img src="assets/img/product-60v-120ah.jpg" alt="60 V lithium battery range" loading="lazy">
        <div class="cat-card__body">
          <p class="tagline">60 V platform</p>
          <h3>60 V &mdash; 30, 60, 67, 100, 120, 166 Ah</h3>
          <p>Rated 64 V with 50 V discharge cut-off. The workhorse platform for scooters,
            tricycles and low-speed electric vehicles.</p>
          <span class="card__link">View 60 V models</span>
        </div>
      </a>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="split">
      <div>
        <p class="eyebrow">Why ZHIFU</p>
        <h2>A battery partner, not just a supplier</h2>
        <p class="lead">Guangdong Zhifu Technology Co., Ltd. has focused on energy storage
          batteries for 15+ years. We design, assemble and test every pack we ship, and we
          handle the documentation your customs broker will ask for.</p>
        <ul class="tick-list">
          <li>Matched cells and an integrated BMS on every pack</li>
          <li>UN38.3 and MSDS compliance for transport</li>
          <li>OEM / ODM with your housing, connector and branding</li>
          <li>Technical support from quotation through to after-sales</li>
        </ul>
        <div class="btn-group">
          <a class="btn btn--outline" href="about.html">About the factory</a>
          <a class="btn btn--outline" href="applications.html">Applications</a>
        </div>
      </div>
      <div class="split__media split__media--duo">
        <img src="assets/img/factory.jpg" alt="Battery assembly line inside the ZHIFU factory" loading="lazy">
        <img src="assets/img/tech.jpg" alt="Battery cell and power electronics technology" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="section section--tint">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Applications</p>
      <h2>Where our batteries are used</h2>
      <p class="lead">From a single scooter pack to a complete commercial storage cabinet.</p>
    </div>
    <div class="grid grid--3">
{apps}
    </div>
  </div>
</section>

{cta}
""".format(stats=stats, certs=certs, cards=cards, feat_html=feat_html,
           apps=apps_html,
           cta=cta_band(0,
                        "Need a quotation for a specific model?",
                        "Send us the model, quantity and destination port and we will reply with "
                        "pricing, lead time and shipping documents."))

    jsonld = [ORG_JSONLD, {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": COMPANY,
        "url": SITE_URL,
        "inLanguage": "en",
    }]
    return page(0,
                "ZHIFU | 60V & 72V Lithium Battery Packs for EV & Energy Storage",
                "ZHIFU manufactures 60 V and 72 V lithium-ion battery packs from 30 Ah to 166 Ah "
                "for electric motorcycles, tricycles, low-speed EVs, golf cars and energy storage. "
                "Browse the full range online and request a quotation.",
                "index.html", body, "home", jsonld=jsonld)


def build_products():
    cards = "\n".join(product_card(p, 0) for p in PRODUCTS)
    body = """{hero}

<section class="section">
  <div class="container">
    <div class="filterbar" id="filterBar">
      <div class="filter-group">
        <span>Voltage</span>
        <button class="chip is-active" type="button" data-filter-voltage="all">All</button>
        <button class="chip" type="button" data-filter-voltage="60">60 V</button>
        <button class="chip" type="button" data-filter-voltage="72">72 V</button>
      </div>
      <div class="filter-group">
        <span>Capacity</span>
        <button class="chip is-active" type="button" data-filter-capacity="all">All</button>
        <button class="chip" type="button" data-filter-capacity="low">30 Ah</button>
        <button class="chip" type="button" data-filter-capacity="mid">60 &ndash; 67 Ah</button>
        <button class="chip" type="button" data-filter-capacity="high">100 Ah +</button>
      </div>
      <div class="filter-search">
        {searchicon}
        <input type="search" id="productSearch" placeholder="Search model or application&hellip;" aria-label="Search products">
      </div>
    </div>

    <p class="results-count" id="resultsCount">12 products</p>

    <div class="grid grid--3" id="productGrid">
{cards}
    </div>

    <div class="empty-state" id="emptyState" hidden>
      <h3>No matching models</h3>
      <p>Try a different filter, or <a href="contact.html">ask us for a custom pack</a>.</p>
    </div>

    <div class="section--tight"></div>
    <div class="note-inline">
      <strong>Need a different voltage or capacity?</strong> We build custom packs (OEM / ODM) to
      your specification &mdash; send us your requirements through the
      <a href="contact.html">quotation form</a>.
    </div>
  </div>
</section>

{cta}
""".format(hero=page_hero("Lithium battery products",
                          "Full range of 60 V and 72 V lithium-ion battery packs, 30 Ah to 166 Ah. "
                          "Filter by voltage or capacity, then open a model for full specifications.", 0),
           cards=cards, searchicon=icon("search"),
           cta=cta_band(0, "Not sure which pack fits your vehicle?",
                        "Tell us the vehicle type, motor power and daily range. We will recommend "
                        "the right voltage and capacity."))

    # anchor targets used by the home page (#v72 / #v60)
    body = body.replace('<div class="grid grid--3" id="productGrid">',
                        '<span id="v72"></span><span id="v60"></span>\n    <div class="grid grid--3" id="productGrid">')

    return page(0,
                "Products | 60V & 72V Lithium Battery Packs (30\u2013166 Ah) \u2014 ZHIFU",
                "Browse all ZHIFU lithium-ion battery packs: 60 V and 72 V, 30 Ah to 166 Ah, with "
                "full technical specifications, applications and quotation requests.",
                "products.html", body, "products",
                jsonld=breadcrumb_jsonld([("Home", "index.html"), ("Products", "products.html")]))


def build_product(p):
    related = [q for q in PRODUCTS if q["slug"] != p["slug"]]
    related = sorted(related, key=lambda q: (abs(q["capacity"] - p["capacity"]), abs(q["voltage"] - p["voltage"])))[:3]
    rel_cards = "\n".join(product_card(q, 1) for q in related)
    apps = "\n".join('<li>%s</li>' % e(a) for a in p["applications"])
    highlights = "\n".join('<li>%s</li>' % e(h) for h in HIGHLIGHTS)
    spec_props = [
        {"@type": "PropertyValue", "name": "Rated voltage", "value": "%.1f V" % p["rated_v"]},
        {"@type": "PropertyValue", "name": "Rated capacity", "value": "%d Ah" % p["capacity"]},
        {"@type": "PropertyValue", "name": "Rated energy", "value": "%s Wh" % format(p["energy"], ",")},
        {"@type": "PropertyValue", "name": "Maximum continuous discharge current", "value": "%d A" % p["max_dis"]},
        {"@type": "PropertyValue", "name": "Peak current (2 s)", "value": "%d A" % p["peak"]},
        {"@type": "PropertyValue", "name": "Charging mode", "value": CHARGE_MODE},
    ]
    product_ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "%s lithium-ion battery pack" % p["model"],
        "sku": p["slug"],
        "mpn": p["model"].replace(" ", ""),
        "brand": {"@type": "Brand", "name": BRAND},
        "manufacturer": {"@type": "Organization", "name": COMPANY},
        "category": "Lithium-ion battery pack",
        "description": ("%s rechargeable lithium-ion battery pack (%s Wh) for %s. "
                        "Integrated BMS, UN38.3 and MSDS compliant, OEM/ODM available."
                        % (p["model"], format(p["energy"], ","), ", ".join(p["applications"]).lower())),
        "image": [SITE_URL + "/assets/img/product-" + p["slug"] + ".jpg"],
        "additionalProperty": spec_props,
    }

    body = """<div class="container">
  <nav class="crumbs" aria-label="Breadcrumb">
    <a href="{home}">Home</a><span>/</span>
    <a href="{products}">Products</a><span>/</span>
    <span>{model}</span>
  </nav>
</div>

<section class="container">
  <div class="detail">
    <div class="detail__media">
      <span class="detail__badge">{voltage} V platform</span>
      <img src="{img}" alt="{model} lithium-ion battery pack" width="1400" height="1070">
    </div>
    <div>
      <p class="eyebrow">ZHIFU lithium-ion battery pack</p>
      <h1>{model} lithium battery</h1>
      <p class="detail__sub">Rechargeable lithium-ion battery pack &middot; {energy} Wh &middot;
        integrated BMS &middot; UN38.3 / MSDS compliant</p>
      <div class="key-specs">
        <div class="key-spec"><span>Rated voltage</span><b>{rated_v} V</b></div>
        <div class="key-spec"><span>Rated capacity</span><b>{capacity} Ah</b></div>
        <div class="key-spec"><span>Rated energy</span><b>{energy} Wh</b></div>
        <div class="key-spec"><span>Peak current (2 s)</span><b>{peak} A</b></div>
      </div>
      <p class="detail__sub" style="margin-bottom:10px"><strong>Typical applications</strong></p>
      <ul class="chips">{apps}</ul>
      <div class="btn-group">
        <a class="btn" href="{quote}">Request a quotation</a>
        <a class="btn btn--outline" href="{wa}" target="_blank" rel="noopener">WhatsApp enquiry</a>
      </div>
    </div>
  </div>
</section>

<section class="section section--tint">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Specifications</p>
      <h2>{model} technical data</h2>
      <p class="lead">Values below are taken from the printed ZHIFU product manual. Custom
        configurations are available on request.</p>
    </div>
    {spec}
    <div class="note-inline" style="margin-top:20px">
      All models are supplied with an integrated BMS and are produced to order. Please confirm
      connector type, housing dimensions and communication interface with our sales team before
      ordering.
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="split">
      <div>
        <p class="eyebrow">Applications</p>
        <h2>Where the {model} is used</h2>
        <ul class="chips" style="margin-top:18px">{apps}</ul>
        <ul class="tick-list" style="margin-top:24px">
{highlights}
        </ul>
      </div>
      <div class="split__media">
        <img src="{img}" alt="{model} battery pack in a real application" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="section section--tint">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Related models</p>
      <h2>Other packs you may need</h2>
    </div>
    <div class="grid grid--3">
{rel_cards}
    </div>
  </div>
</section>

{cta}
""".format(home=rel(1, "index.html"), products=rel(1, "products.html"),
           model=e(p["model"]), tier=e(p["tier"]), voltage=p["voltage"],
           img=rel(1, "assets/img/product-" + p["slug"] + ".jpg"),
           energy=format(p["energy"], ","), rated_v=("%.1f" % p["rated_v"]).rstrip("0").rstrip("."),
           capacity=p["capacity"], peak=p["peak"],
           apps=apps, spec=spec_table(p), highlights=highlights,
           quote=rel(1, "contact.html") + "?model=" + p["model"].replace(" ", "+"),
           wa="https://wa.me/" + WA_NUMBER,
           rel_cards=rel_cards,
           cta=cta_band(1, "Request a %s quotation" % p["model"],
                        "Tell us the quantity and destination port and we will send pricing, lead "
                        "time and shipping documents.", p))

    return page(1,
                "%s Lithium Battery Pack | %s Wh | ZHIFU" % (p["model"], format(p["energy"], ",")),
                "ZHIFU %s rechargeable lithium-ion battery pack: %.1f V rated, %d Ah, %s Wh, "
                "%.0f A continuous discharge, %d A peak. Full specifications and quotation request."
                % (p["model"], p["rated_v"], p["capacity"], format(p["energy"], ","),
                   p["max_dis"], p["peak"]),
                "products/" + p["slug"] + ".html", body, "products",
                og_image=SITE_URL + "/assets/img/product-" + p["slug"] + ".jpg",
                jsonld=[product_ld,
                        breadcrumb_jsonld([("Home", "index.html"),
                                           ("Products", "products.html"),
                                           (p["model"], "products/" + p["slug"] + ".html")])])


def build_applications():
    blocks = [
        ("home", "Household energy storage systems",
         "5 kW, 10 kW and 15 kW lithium battery solutions designed as a direct, higher-cycle-life "
         "alternative to lead-acid household storage. Quiet, maintenance free and ready to pair "
         "with an inverter.",
         ["5 kW / 10 kW / 15 kW system options",
          "Drop-in replacement for lead-acid banks",
          "Lower self-consumption (\u2264 50 \u00b5A per pack)",
          "Stackable capacity for longer autonomy"],
         "product-72v-120ah.jpg", False),
        ("truck", "Special vehicle batteries",
         "Reliable power packs specifically engineered for golf cars, sightseeing cars, electric "
         "motorcycles, tricycles, quadricycles and recreational vehicles.",
         ["Golf cars and sightseeing cars",
          "Electric motorcycles and scooters",
          "Cargo and passenger tricycles",
          "Quadricycles and recreational vehicles"],
         "product-72v-100ah.jpg", True),
        ("factory", "Commercial &amp; industrial (C&amp;I) storage",
         "Scalable battery systems carefully designed to provide exceptional energy reliability "
         "and efficiency for commercial and industrial sites, from peak shaving to backup.",
         ["Modular, scalable capacity",
          "High continuous discharge current",
          "Backup and peak-shaving duty",
          "Designed for continuous operation"],
         "product-60v-166ah.jpg", False),
        ("sun", "Solar energy storage integration",
         "Efficient and sustainable batteries designed for seamless integration with renewable "
         "energy systems, supporting a greener and more sustainable future.",
         ["Compatible with solar inverters",
          "Store daytime generation for night use",
          "CC&CV charging profile",
          "Suitable for off-grid and hybrid systems"],
         "product-60v-120ah.jpg", True),
        ("layers", "Customised battery solutions (OEM / ODM)",
         "Tailored designs that meet your specific application requirements \u2014 from housing and "
         "connector type to communication protocol, label and packaging.",
         ["Custom housing and mounting",
          "Connector and cable configuration",
          "Communication interface options",
          "Private-label branding"],
         "product-72v-166ah.jpg", False),
    ]
    html_blocks = []
    for ic, title, text, bullets, img, reverse in blocks:
        bl = "\n".join('<li>%s</li>' % e(b) for b in bullets)
        html_blocks.append("""<section class="section{alt}">
  <div class="container">
    <div class="split{rev}">
      <div>
        <p class="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p class="lead">{text}</p>
        <ul class="tick-list">{bl}</ul>
        <a class="btn btn--outline" href="products.html">See matching battery packs</a>
      </div>
      <div class="split__media">
        <img src="assets/img/{img}" alt="{title}" loading="lazy">
      </div>
    </div>
  </div>
</section>""".format(alt=" section--tint" if reverse else "",
                    rev=" split--reverse" if reverse else "",
                    eyebrow=title, title=e(title), text=e(text), bl=bl, img=img))

    body = page_hero("Applications",
                     "Five ways customers use ZHIFU batteries \u2014 household storage, special "
                     "vehicles, commercial and industrial storage, solar integration and fully "
                     "customised packs.", 0) + "\n\n" + "\n\n".join(html_blocks) + "\n\n" + \
        cta_band(0, "Tell us about your application",
                 "Vehicle type, motor power, daily range or system size \u2014 we will recommend the "
                 "right voltage and capacity.")

    return page(0,
                "Applications | Household, Vehicle, C&I & Solar Storage \u2014 ZHIFU",
                "ZHIFU lithium batteries are used in household energy storage, golf cars, "
                "sightseeing cars, electric motorcycles and tricycles, low-speed EVs, commercial "
                "and industrial storage and solar systems.",
                "applications.html", body, "applications",
                jsonld=breadcrumb_jsonld([("Home", "index.html"),
                                          ("Applications", "applications.html")]))


def build_about():
    stats = "\n".join(
        '<div class="stat"><b>%s</b><span>%s</span></div>' % (e(v), e(l)) for v, l in STATS)
    certs = "\n".join('<li class="cert">%s</li>' % e(c) for c in CERTIFICATIONS)
    body = """{hero}

<section class="section">
  <div class="container">
    <div class="split">
      <div>
        <p class="eyebrow">About us</p>
        <h2>Manufacturing power batteries in Huizhou since 2005</h2>
        <p class="lead">Situated in the vibrant manufacturing hub of Huizhou, China, Guangdong
          Zhifu Technology Co., Ltd. shines as a beacon of innovation and excellence in crafting power
          batteries and energy storage solutions.</p>
        <p>Our extensive years of dedicated manufacturing and pioneering R&amp;D expertise allow us
          to specialise in high-performance lithium-ion batteries, meticulously engineered to meet
          the ever-evolving demands of the global market. With our technologies and an unwavering
          commitment to quality, we deliver energy solutions worldwide.</p>
        <div class="stat-row">{stats}</div>
      </div>
      <div class="split__media">
        <img src="assets/img/building-circle.png" alt="ZHIFU Technology offices" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="section section--tint">
  <div class="container">
    <div class="split split--reverse">
      <div>
        <p class="eyebrow">Corporate characteristics</p>
        <h2>Inside the factory</h2>
        <ul class="tick-list">
          <li>Focused on the energy storage battery industry for over 15 years</li>
          <li>Projects delivered across more than 100 countries</li>
          <li>A 5,000 m\u00b2 factory building in Huizhou, Guangdong</li>
          <li>More than 100 employees across production, R&amp;D and quality</li>
        </ul>
        <ul class="trust__list" style="margin-top:24px">{certs}</ul>
      </div>
      <div class="split__media split__media--duo">
        <img src="assets/img/factory.jpg" alt="Battery cell assembly line" loading="lazy">
        <img src="assets/img/applications.jpg" alt="Vehicles powered by ZHIFU batteries" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head section-head--center">
      <p class="eyebrow">Quality &amp; compliance</p>
      <h2>Documentation ready for export</h2>
      <p class="lead">Our packs are tested and certified so they clear customs and travel safely,
        by air or by sea.</p>
    </div>
    <div class="grid grid--4">
      <div class="feature"><div class="feature__icon">{i_shield}</div><h3>Certified products</h3>
        <p>CE, CB, CCC, FC, MSDS and UN38.3 available for the range.</p></div>
      <div class="feature"><div class="feature__icon">{i_layers}</div><h3>Matched cells</h3>
        <p>Cells are capacity-sorted and matched before assembly for consistent pack performance.</p></div>
      <div class="feature"><div class="feature__icon">{i_bolt}</div><h3>Tested packs</h3>
        <p>Every pack is checked for voltage, internal resistance and function before packing.</p></div>
      <div class="feature"><div class="feature__icon">{i_truck}</div><h3>Export support</h3>
        <p>UN38.3 report, MSDS, packing list and commercial invoice supplied with your order.</p></div>
    </div>
  </div>
</section>

{cta}
""".format(hero=page_hero("About ZHIFU Technology",
                          "Guangdong Zhifu Technology Co., Ltd. \u2014 a lithium-ion power battery "
                          "manufacturer in Huizhou, Guangdong, serving more than 100 countries.", 0),
           stats=stats, certs=certs,
           i_shield=icon("shield"), i_layers=icon("layers"), i_bolt=icon("bolt"),
           i_truck=icon("truck"),
           cta=cta_band(0, "Planning a project?",
                        "Send us your technical requirements and we will come back with a model "
                        "recommendation, pricing and lead time."))

    return page(0,
                "About Us | Guangdong Zhifu Technology Co., Ltd. (ZHIFU)",
                "ZHIFU (Guangdong Zhifu Technology Co., Ltd.) is a lithium-ion power battery "
                "manufacturer in Huizhou, China: 15+ years of experience, 5,000 m\u00b2 factory, "
                "100+ employees and projects in 100+ countries.",
                "about.html", body, "about",
                jsonld=[ORG_JSONLD,
                        breadcrumb_jsonld([("Home", "index.html"), ("About", "about.html")])])


def build_contact():
    options = "\n".join(
        '<option value="%s"%s>%s</option>' % (e(p["model"]), ' selected' if i == 0 else '', e(p["model"]))
        for i, p in enumerate(PRODUCTS))
    body = """{hero}

<section class="section">
  <div class="container">
    <div class="contact-grid">
      <div class="form-card">
        <h2 style="margin-bottom:6px">Request a quotation</h2>
        <p class="lead" style="font-size:.95rem">Fill in the form and we will reply with pricing,
          lead time and shipping documents. Typical response time: within one working day.</p>
        <form id="inquiryForm" novalidate>
          <div class="field">
            <label for="fieldProductSelect">Product of interest</label>
            <select id="fieldProductSelect" name="product">
              <option value="">General enquiry / not sure yet</option>
{options}
            </select>
            <input type="hidden" id="fieldProduct" name="productText" value="">
          </div>
          <div class="field-row">
            <div class="field">
              <label for="fieldName">Your name *</label>
              <input type="text" id="fieldName" name="name" autocomplete="name" required>
            </div>
            <div class="field">
              <label for="fieldEmail">Email *</label>
              <input type="email" id="fieldEmail" name="email" autocomplete="email" required>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label for="fieldQuantity">Quantity (pcs)</label>
              <input type="text" id="fieldQuantity" name="quantity" inputmode="numeric">
            </div>
            <div class="field">
              <label for="fieldCountry">Country / port</label>
              <input type="text" id="fieldCountry" name="country">
            </div>
          </div>
          <div class="field">
            <label for="fieldCompany">Company</label>
            <input type="text" id="fieldCompany" name="company" autocomplete="organization">
          </div>
          <div class="field">
            <label for="fieldMessage">Requirements</label>
            <textarea id="fieldMessage" name="message" placeholder="Vehicle type, motor power, required voltage &amp; capacity, connector, target price, delivery port&hellip;"></textarea>
          </div>
          <div class="btn-group">
            <button class="btn" type="submit">Send enquiry</button>
            <button class="btn btn--outline" type="button" id="whatsappSend">Send on WhatsApp</button>
          </div>
          <p class="form-note">This form opens your own email app or WhatsApp with the details
            pre-filled &mdash; nothing is sent anywhere until you press send.</p>
          <p class="form-status" id="formStatus" role="status" aria-live="polite"></p>
        </form>
      </div>

      <div>
        <div class="info-card">
          <h3>Contact details</h3>
          <ul class="info-list">
            <li><span class="ico">{i_mail}</span><div><b>Email</b><a href="mailto:{email}">{email}</a></div></li>
            <li><span class="ico">{i_phone}</span><div><b>Phone</b><a href="tel:{phone_tel}">{phone}</a></div></li>
            <li><span class="ico">{i_chat}</span><div><b>WhatsApp</b><a href="{wa}" target="_blank" rel="noopener">{whatsapp}</a></div></li>
            <li><span class="ico">{i_pin}</span><div><b>Factory</b><span>{address}</span></div></li>
          </ul>
        </div>

        <div class="qr-card" style="background:#0d63d4">
          <div style="flex:1">
            <h3>Share this catalogue</h3>
            <p>Send the link to a colleague or open the native share sheet.</p>
            <div class="btn-group" style="margin-top:14px">
              <button class="btn btn--light btn--sm" type="button" id="shareBtn">Share</button>
              <button class="btn btn--ghost btn--sm" type="button" data-copy>Copy link</button>
            </div>
          </div>
        </div>

        <div class="info-card">
          <h3>Prefer to talk?</h3>
          <p style="font-size:.94rem;color:var(--ink-2)">Our export team speaks English and Chinese.
            Tell us the model and quantity for a fast, firm quotation.</p>
          <div class="btn-group">
            <a class="btn btn--outline btn--sm" href="mailto:{email}">Email us</a>
            <a class="btn btn--outline btn--sm" href="{wa}" target="_blank" rel="noopener">WhatsApp</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
""".format(hero=page_hero("Contact & quotation",
                          "Send us your requirements and we will reply with pricing, lead time and "
                          "shipping documents \u2014 usually within one working day.", 0),
           options=options,
           i_mail=icon("mail"), i_phone=icon("phone"), i_chat=icon("chat"),
           i_pin=icon("pin"),
           email=e(EMAIL), phone=e(PHONE), phone_tel=e(PHONE.replace(" ", "")),
           whatsapp=e(WHATSAPP), wa="https://wa.me/" + WA_NUMBER,
           address=e(ADDRESS))

    return page(0,
                "Contact & Quotation | ZHIFU Lithium Battery Manufacturer",
                "Contact ZHIFU for lithium battery quotations by email, phone or WhatsApp, "
                "or use the pre-filled enquiry form.",
                "contact.html", body, "contact",
                jsonld=[ORG_JSONLD,
                        breadcrumb_jsonld([("Home", "index.html"), ("Contact", "contact.html")])])


def build_robots():
    return "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL.rstrip("/")


def build_sitemap():
    urls = [("index.html", "1.0"), ("products.html", "0.9"), ("applications.html", "0.8"),
            ("about.html", "0.7"), ("contact.html", "0.8")]
    urls += [("products/" + p["slug"] + ".html", "0.8") for p in PRODUCTS]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio in urls:
        parts.append("  <url><loc>%s/%s</loc><priority>%s</priority></url>"
                     % (SITE_URL.rstrip("/"), path, prio))
    parts.append("</urlset>")
    return "\n".join(parts) + "\n"


def write(path, content):
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  wrote %s" % path)


def main():
    print("Building ZHIFU catalogue for %s" % SITE_URL)
    write("index.html", build_index())
    write("products.html", build_products())
    for p in PRODUCTS:
        write("products/%s.html" % p["slug"], build_product(p))
    write("applications.html", build_applications())
    write("about.html", build_about())
    write("contact.html", build_contact())
    write("robots.txt", build_robots())
    write("sitemap.xml", build_sitemap())
    print("Done.")


if __name__ == "__main__":
    main()

