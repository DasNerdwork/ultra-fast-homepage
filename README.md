# DasNerdwork.net - Ultra-Fast One-Pager

A minimalist, framework-free one-pager displaying live status of servers and APIs. Optimized for ultra-fast first paint, minimal JavaScript overhead, and direct API requests.

<img width="428" height="138" alt="image" src="https://github.com/user-attachments/assets/4aed064e-be5b-4d78-9be5-d5113babf3b7" />

---

## Features

- Live status for servers & APIs
- Price tracking for heating oil, electricity, petrol & bitcoin
- Charts via ApexCharts with selectable timeframes (7, 30, 90 days)
- Dark/Light mode toggle with local storage
- Minimal JS & CSS footprint (TailwindCSS & Flowbite)
- Responsive layout for all screen sizes
- Raw data view (debug) using `<details>` tag
- No frameworks required
- Responsive layout for all screen sizes

---

## Project Structure

This project has a simple and minimalistic project structure without the need for many components because of it's rather small dimensions:

```
/
├─ api/                 # Backend endpoints for live status
├─ assets/              
│  ├─ css/              # TailwindCSS output + Flowbite CSS
│  ├─ js/               # main.js, Flowbite, ApexCharts
│  └─ img/              # Favicons & other images
├─ datenschutz.html     # Privacy policy
├─ impressum.html       # Legal notice / imprint
├─ index.html           # Main one-pager
├─ package.json         # Node.js dependencies
├─ package-lock.json    # Lockfile
└─ .gitignore           # Ignored files (node_modules, .env)
```

---

## Live Status

Services displayed in the grid, e.g.:

- Teamspeak Server
- Satisfactory Server
- Garry's Mod Server
- Minecraft Server
- SinusBot / Phantombot
- Nextcloud, Home Assistant, UniFi Controller
- Pi-hole

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
