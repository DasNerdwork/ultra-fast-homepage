# DasNerdwork.net - Ultra-Fast One-Pager

A minimalist, framework-free one-pager displaying live prices and real-time status of self-hosted servers and APIs. Optimized for ultra-fast first paint, minimal JavaScript overhead, and a perfect Lighthouse score.

<img width="428" height="138" alt="image" src="https://github.com/user-attachments/assets/4aed064e-be5b-4d78-9be5-d5113babf3b7" />

**Lighthouse: 100 / 100 / 100 / 100** (Performance, Accessibility, Best Practices, SEO) on desktop and mobile.

---

## Features

- Live status for servers & APIs (HTTP + TCP health checks, auto-refresh)
- Price tracking for heating oil, petrol, Bitcoin & ETFs
- Live petrol prices respecting the German "12-Uhr-Regel" (daily low before noon, post-noon high, current price via Tankerkönig)
- Charts via ApexCharts with selectable timeframes (7, 30, 90 days)
- Dark/Light mode toggle with local storage
- Critical CSS inlined at build time, zero render-blocking stylesheets beyond first paint
- Preconnect & preload hints so API requests start in parallel with JS download
- Strict Content Security Policy (no inline scripts)
- LLM-friendly site overview via [`/llms.txt`](https://dasnerdwork.net/llms.txt)
- Responsive layout, no frameworks required

---

## Architecture

- **Frontend**: Vanilla JS + TailwindCSS + Flowbite components, served as static files via Nginx
- **Backend**: FastAPI (Python) + PostgreSQL behind Nginx with per-IP rate limiting
- **Data ingestion**: Cron-based fetch scripts (Tankerkönig, heizoel24, CoinGecko, yfinance) writing daily prices to PostgreSQL
- **API**: Public REST API at [api.dasnerdwork.net/docs](https://api.dasnerdwork.net/docs) with server-side caching (15 min live prices, 30 s status checks) and cache-control headers

## Project Structure

```
/
├─ api/ # FastAPI backend
│ ├─ main.py # App, CORS, cache middleware, custom Swagger UI
│ ├─ db.py # Shared PostgreSQL connection pool
│ ├─ routers/ # Endpoints: oil, petrol, btc, etfs, status
│ └─ utils/ # Cron fetch scripts & status checks
├─ static/ # Web root (served by Nginx)
│ ├─ assets/ # CSS, JS, images
│ ├─ index.html # GENERATED - do not edit directly
│ ├─ llms.txt # LLM-friendly site overview
│ ├─ datenschutz.html # Privacy policy
│ └─ impressum.html # Legal notice / imprint
├─ index.template.html # Source template for index.html
├─ build-html.mjs # Inlines critical CSS into index.html
└─ package.json # Build scripts & dependencies
```

## Build

`static/index.html`, `static/assets/css/output.css` and `static/assets/js/main.min.js` are build artifacts and not tracked in git. After cloning or pulling:

```bash
npm install
npm run dev        # builds CSS, minifies JS, generates index.html with inlined CSS
```

Individual steps: `npm run build:css`, `npm run build:js`, `npm run build:html`.
After updating ApexCharts: `npm run build:vendor` re-minifies the vendor bundle with a source map.

**Important:** edit `index.template.html`, never `static/index.html` - the latter is overwritten on every build.

---

## Live Status

Services displayed in the grid, e.g.:

- Teamspeak Server
- Satisfactory Server
- Garry's Mod Server
- Minecraft Server (Vanilla & Modpack)
- SinusBot / Phantombot
- Nextcloud, Home Assistant, UniFi Controller
- Pi-hole, Netdata

#### Status indicators:

Services are __color-coded__:
- 🟢 Up - Online
- 🟡 Partly - Partially available
- 🔴 Down - Offline
- ⚪ Unknown - Status Unknown

---

## License

This project is private, no license granted. No third-party usage allowed.

#### Authors

Florian Falk - Alias: TheNerdwork / DasNerdwork
Website: https://dasnerdwork.net