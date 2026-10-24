# ZHIFU Technology — online product catalogue (H5)

A complete, self-contained static website that replaces the printed English PDF
product manual. No server, database, framework or build tool is required at
runtime — upload the folder to any host and it works on phones, tablets and
desktops.

---

## 1. What is in this folder

```
index.html                  Home page (brand, core products, platforms, CTA)
products.html               Full range with voltage / capacity filters + search
products/<model>.html       12 product detail pages (specs, applications, enquiry)
applications.html           The five business areas
about.html                  Company profile, factory, certifications
contact.html                Enquiry form, contact details, QR code, share buttons
assets/css/style.css        All styling (hand written, no framework)
assets/js/site.js           Navigation, filters, enquiry form, QR, share
assets/js/qrcode-lite.js    Offline QR encoder (no CDN, no network needed)
assets/img/                 Product photos and brand images
assets/docs/                Original English product manual (PDF, optional download)
tools/make-qr.js            Generate QR code files (SVG + PNG) for print
build.py                    Regenerates every HTML page from the data in it
robots.txt, sitemap.xml     SEO files
```

## 2. Preview locally

Any static file server works:

```bash
cd <this folder>
python -m http.server 8080
# then open http://localhost:8080
```

## 3. Publish

Upload the **whole folder** (not only `index.html`) to any static host:

| Host | How |
|---|---|
| Netlify | Drag the folder onto <https://app.netlify.com/drop> |
| Cloudflare Pages | Create project → *Direct upload* → drop the folder |
| Vercel | `npx vercel --prod` inside the folder |
| GitHub Pages | Push the folder to a repo, enable Pages on the branch |
| Alibaba Cloud OSS / Tencent COS | Enable *static website hosting*, upload the folder |
| Your own nginx / Apache | Copy the folder into the web root |

No server-side code, PHP or database is needed. HTTPS is recommended (free on
all hosts above).

## 4. Change your contact details

Open `build.py`, edit the **SITE CONFIG** block at the top, then run:

```bash
python build.py
```

| Variable | Meaning | Current placeholder |
|---|---|---|
| `SITE_URL` | Public domain, used for canonical URLs, sitemap and the QR code | `https://www.wenrey-battery.com` |
| `EMAIL` | Sales inbox | `yizong2023@outlook.com` |
| `PHONE` | Public phone number | `+86 15826560159` |
| `WHATSAPP` | WhatsApp number, digits only, country code first | `+86 15826560159` |
| `ADDRESS` | Factory address | Huiyang District, Huizhou |
| `WECHAT` | WeChat ID | `zhifu-sales` |

If you do not want to run Python, you can also just search-and-replace those
strings directly inside the generated `.html` files.

## 5. Optional printed QR codes

The Contact page does not display a QR block. The QR generator is retained only
for optional printed brochures, exhibition material and name cards:

```bash
node tools/make-qr.js "https://your-domain.com" --name website --scale 12
node tools/make-qr.js "https://your-domain.com/products/72v-100ah.html" --name 72v-100ah --scale 12
```

This writes `website.svg` (vector, best for print) and `website.png` next to
each other. Print at least 2 × 2 cm and keep the white margin.

## 6. Adding or editing products

Products live in the `PRODUCTS` list in `build.py`. Add a dictionary, drop a
matching photo at `assets/img/product-<slug>.jpg`, run `python build.py`, done.
The product grid, the detail page, the sitemap and all internal links update
themselves.

## 7. SEO checklist after you go live

1. Replace `SITE_URL` with the real domain and re-run `build.py`.
2. Add the site to [Google Search Console](https://search.google.com/search-console)
   and submit `https://your-domain.com/sitemap.xml`.
3. Add the link to your LinkedIn company page and email signature.
4. Keep the product pages indexed — each one has its own title, description,
   canonical URL and `Product` structured data (JSON-LD).

## 8. Notes

* The enquiry form does not use a backend: it opens the visitor's own mail app
  or WhatsApp with everything pre-filled. If you prefer a real form endpoint
  (Formspree, EmailJS, your own API), replace the submit handler in
  `assets/js/site.js`.
* Product data was transcribed from the printed English product manual. Please
  have it reviewed before publishing (see `核对清单.md`).
* All images were extracted from the supplied PDF/PPT source material.
