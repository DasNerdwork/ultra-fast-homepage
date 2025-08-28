# DasNerdwork.net - Ultra-Fast One-Pager

A minimalist, framework-free one-pager showing live status of your servers and APIs. Optimized for maximum speed, minimal JavaScript overhead, and fast first paint.

---

## Features

- Live status for servers & APIs
- No caching, direct API requests
- Parallel requests with timeout, retries & abort on tab switch
- Heating oil price chart via ApexCharts
- Dark/Light mode toggle with local storage
- Minimal JS & CSS, uses TailwindCSS utilities
- Raw data view (debug) using `<details>` tag
- Responsive layout for all screen sizes

---

## Project Structure

This project has a simple and minimalistic project structure without the need for many components because of it's rather small dimensions:

```
/
├─ api/ # Backend endpoints for live status
├─ assets/ # CSS, JS, images
├─ datenschutz.html # Privacy policy
├─ impressum.html # Legal notice / imprint
├─ index.html # Main one-pager
├─ package.json # Node.js dependencies
├─ package-lock.json # Node.js lockfile
└─ .gitignore # Ignored files (node_modules, .env)
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

#### Status indicators (color-coded):

- 🟢 Up
- 🟡 Partly
- 🔴 Down
- ⚪ Unknown

---

## License

This project is private, no license granted. No third-party usage allowed.

#### Authors

Florian Falk - Alias: TheNerdwork / DasNerdwork
Website: https://dasnerdwork.net