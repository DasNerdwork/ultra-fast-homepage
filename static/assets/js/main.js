const API_BASE = 'https://api.dasnerdwork.net/v1';
const grid = document.getElementById('status-grid');
const raw = document.getElementById('raw');
// Liste der Services
const services = [
{ id: "teamspeak", name: "Teamspeak" },
{ id: "mc-vanilla", name: "MC Vanilla" },
{ id: "musikbot", name: "Musikbot" },
{ id: "clashscout", name: "Clashscout" },
{ id: "voidwatch", name: "Voidwatch" },
{ id: "pb-smetti", name: "Pb Smetti" },
{ id: "pb-junky", name: "Pb Junky" },
{ id: "pb-orphi", name: "Pb Orphi" },
{ id: "pb-snacky", name: "Pb Snacky" },
{ id: "nextcloud", name: "Nextcloud" },
{ id: "homeassistant", name: "Homeassistant" },
{ id: "unifi", name: "Unifi" },
{ id: "pihole", name: "Pihole" },
{ id: "satisfactory", name: "Satisfactory" },
{ id: "gmod", name: "Gmod" },
{ id: "mc-modpack", name: "MC Modpack" }
];

services.forEach(svc => {
grid.appendChild(cardSkeleton(svc));
});

document.getElementById("year").textContent = new Date().getFullYear();

// Alle Dropdown-Links abfangen
document.querySelectorAll('[id^="lastDaysdropdown-"] a').forEach(link => {
link.addEventListener('click', e => {
    e.preventDefault(); // verhindert das Springen nach oben
    const selected = link.textContent.trim();

    // Dropdown-Button finden (über aria-labelledby)
    const dropdown = link.closest('div[id^="lastDaysdropdown-"]');
    const buttonId = link.closest('ul').getAttribute('aria-labelledby');
    const button = document.getElementById(buttonId);
    if (button) {
    const textSpan = button.querySelector('.dropdown-text');
    if (textSpan) textSpan.textContent = selected;
    }
    if (dropdown) {
    dropdown.classList.add('hidden');
    }

    // Hier den Chart neu rendern
    if (dropdown.id.includes('oil')) {
    renderApiChart({
        apiPath: `${API_BASE}/oil`,
        valueKey: "price_eur",
        chartTitle: "Heizölpreis",
        headerSelector: "#oil-header",
        changeSelector: "#oil-change",
        chartSelector: "#oil-chart",
        last: parseInt(selected.match(/\d+/)[0]),
    });
    } else if (dropdown.id.includes('energy')) {
    renderApiChart({
        apiPath: `${API_BASE}/energy`,
        valueKey: "price_ct_per_kwh",
        chartTitle: "Strompreis",
        headerSelector: "#energy-header",
        changeSelector: "#energy-change",
        chartSelector: "#energy-chart",
        last: parseInt(selected.match(/\d+/)[0])
    });
    } else if (dropdown.id.includes('petrol')) {
    renderApiChart({
        apiPath: `${API_BASE}/petrol`,
        valueKey: "e5",
        chartTitle: "Benzinpreis",
        headerSelector: "#petrol-header",
        changeSelector: "#petrol-change",
        chartSelector: "#petrol-chart",
        last: parseInt(selected.match(/\d+/)[0])
    });
    } else if (dropdown.id.includes('bitcoin')) {
    renderApiChart({
        apiPath: `${API_BASE}/btc`,
        valueKey: "price_eur",
        chartTitle: "Bitcoinpreis",
        headerSelector: "#bitcoin-header",
        changeSelector: "#bitcoin-change",
        chartSelector: "#bitcoin-chart",
        last: parseInt(selected.match(/\d+/)[0]),
        formatValue: (val) => formatEuro(val, 0), // Funktion ohne Nachkommastellen
        colorUpDown: true
    });
    }
});
});

// Hilfsfunktion: Badge für Status
function badgeStatus(status) {
    switch (status) {
        case 'green': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full text-green-200 bg-green-800/60">● OK</span>';
        case 'yellow': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-800">● Warning</span>';
        case 'red': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full text-red-200 bg-red-900/70 ">● Offline</span>';
        default: return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-zinc-100 text-zinc-800">● Unknown</span>';
        }
}

// case 'green': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full text-green-800 bg-green-900/40 dark:text-green-200">● OK</span>';
// case 'yellow': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200">● Warning</span>';
// case 'red': return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full text-red-800 bg-red-900/40 dark:text-red-200">● Offline</span>';
// default: return '<span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-zinc-100 text-zinc-800 dark:bg-zinc-800/40 dark:text-zinc-200">● Unknown</span>';

// Karte für einen Service rendern
function renderCard(name, id, data) {
const el = document.createElement('article');
el.className = 'rounded-2xl p-4';

let serviceStatus = deriveStatus(data);

let html = `
    <div class="flex items-center justify-between gap-3">
    <h3 class="font-semibold">${name}</h3>
    ${data.instances ? '' : badgeStatus(serviceStatus)}
    </div>
`;

if (data.instances) {
    // Mehrfach-Instanzen (z.B. Phantombot)
    html += `<div class="mt-2 space-y-1 text-sm">`;
    data.instances.forEach((inst, i) => {
    html += `
        <div class="flex items-center gap-2">
        <span>${inst.name || 'Instance ' + (i + 1)}</span>
        ${badgeStatus(inst.status)}
        </div>
    `;
    });
    html += `</div>`;
} else {
    // HTTP + TCP Infos
    let details = [];
    if (data.http) {
    details.push(`HTTP: ${data.http.httpStatus ?? '—'} ${data.http.ok ? '' : '-'}`);
    }
    if (data.tcp) {
    details.push(`TCP: ${data.tcp.ok ? data.tcp.ms + ' ms' : '-'}`);
    }
    html += `<div class="mt-2 text-sm text-text/70 dark:text-text/40">${details.join(' | ')}</div>`;
}

el.innerHTML = html;
return el;
}

function deriveStatus(data) {
// Mehrfach-Instanzen → Status schon direkt drin
if (data.instances) {
    return null;
}

const httpOk = data.http?.ok ?? null;
const tcpOk = data.tcp?.ok ?? null;

if (httpOk === false || tcpOk === false) {
    return 'red';
}
if (httpOk === true || tcpOk === true) {
    return 'green';
}
return 'yellow'; // unbekannt / keine Daten
}

// Status laden
async function loadStatus() {
try {
    const res = await fetch(`${API_BASE}/status`);
    const json = await res.json();

    // Debug
    raw.textContent = JSON.stringify(json, null, 2);

    // Grid leeren
    grid.innerHTML = '';

    // Sortieren: offline = rot → zuletzt
    const entries = Object.entries(json).sort(([idA, dataA], [idB, dataB]) => {
    const statusOrder = { green: 1, yellow: 2, red: 3, null: 2 }; // null = unknown
    const statusA = deriveStatus(dataA) ?? 'yellow';
    const statusB = deriveStatus(dataB) ?? 'yellow';
    return statusOrder[statusA] - statusOrder[statusB];
    });

    // Für jeden Service eine Card erzeugen
    entries.forEach(([id, data]) => {
    const name = id.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    grid.appendChild(renderCard(name, id, data));
    });
} catch (err) {
    console.error("Fehler beim Laden des Status:", err);
}
}

// Initialer Load + Auto-Refresh
loadStatus();
setInterval(loadStatus, 30000);

// UI Helper
document.getElementById("year").textContent = new Date().getFullYear();

function cardSkeleton(svc) {
const el = document.createElement('article');
el.id = `card-${svc.id}`;
el.className = 'min-h-[84px] rounded-2xl p-4 animate-pulse';
el.innerHTML = `
    <div class="h-4 w-28 bg-zinc-200 dark:bg-zinc-800 rounded mb-2"></div>
    <div class="h-3 w-20 bg-zinc-200 dark:bg-zinc-800 rounded"></div>
`;
return el;
}

const formatEuro = (value, decimals = 2) => {
return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
}).format(value);
};

/**
 * Generischer Chart-Renderer für beliebige APIs
 * @param {string} apiPath - z.B. "/v1/oil"
 * @param {string} valueKey - Feldname im JSON, z.B. "price_eur", "price", "e5"
 * @param {string} chartTitle - Titel der Serie im Chart
 * @param {string} headerSelector - Selector für Headerbereich, optional
 * @param {string} chartSelector - Selector für Chart-Container
 * @param {number} last - letzte X Tage
 * @param {Array<string>} valuesPath - optionaler Pfad zum Array, z.B. ["values"] für Oil
 */
async function renderApiChart({ apiPath, valueKey, chartTitle, headerSelector, changeSelector, chartSelector, last = 7, valuesPath = [] }) {
try {
    const res = await fetch(`${apiPath}?last=${last}`);
    const json = await res.json();

    // Falls valuesPath angegeben, Array aus Response extrahieren
    let dataArray = json;
    for (const key of valuesPath) {
    if (dataArray[key] !== undefined) {
        dataArray = dataArray[key];
    } else {
        dataArray = [];
        break;
    }
    }

    // chartData erstellen
    const chartData = dataArray.map(v => ({
    x: typeof v.date === 'number' ? v.date : new Date(v.date).getTime(),
    y: v[valueKey]
    }));

    if (chartData.length === 0) return;

    // Aktueller Wert + Veränderung
    const latestValue = chartData[chartData.length - 1].y;
    const firstValue = chartData[0].y;
    const changePercent = ((latestValue - firstValue) / firstValue * 100).toFixed(2);

    // Header updaten (aktueller Wert)
    if (headerSelector) {
    const headerEl = document.querySelector(headerSelector);
    if (headerEl) {
        if(chartSelector == "#bitcoin-chart") {
        headerEl.querySelector("span").textContent = formatEuro(latestValue, 0);
        } else {
        headerEl.querySelector("span").textContent = formatEuro(latestValue);
        }
    }
    }

    // Change-Box updaten
    if (changeSelector) {
    const changeEl = document.querySelector(changeSelector);
    if (changeEl) {
        const isBitcoin = changeSelector === '#bitcoin-change';
        // Up/Down Farbe für Bitcoin umkehren
        let upClass, downClass;
        if (isBitcoin) {
            upClass = 'text-green-500';   // Bitcoin ↑ = grün
            downClass = 'text-red-400';   // Bitcoin ↓ = rot
        } else {
            upClass = 'text-red-400';     // normal ↑ = rot
            downClass = 'text-green-500'; // normal ↓ = grün
        }
        const isUp = changePercent >= 0;
        changeEl.innerHTML = `
        ${isUp ? '+' : ''}${changePercent}%
        <svg class="w-3 h-3 ms-1" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 10 14">
            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="${isUp ? 'M5 13V1m0 0L1 5m4-4 4 4' : 'M5 1v12m0 0L1 9m4 4 4-4'}"/>
        </svg>
        `;
        changeEl.className =
        `flex items-center px-2.5 py-0.5 text-base font-semibold ${isUp ? upClass : downClass} text-center`;
    }
    }

    // Chart rendern

    let darkFill = localStorage.getItem('theme') === 'light' ? "#cb9150" : "#1C64F2";
    const options = {
    chart: { height: 75, type: "area", fontFamily: "Inter, sans-serif", toolbar: { show: false }, sparkline: { enabled: true } },
    series: [{ name: chartTitle, data: chartData }],
    stroke: { width: 3, curve: 'smooth', colors: [darkFill] },
    fill: { type: "gradient", gradient: { opacityFrom: 0.5, opacityTo: 0, colors: undefined }, colors: [darkFill] },
    xaxis: { type: 'datetime', labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { show: false },
    tooltip: {
        enabled: true,
        followCursor: true,
        marker: { show: true },
        custom: ({ series, seriesIndex, dataPointIndex, w }) => {
        const point = w.config.series[seriesIndex].data[dataPointIndex];
        const val = point.y;
        const date = new Date(point.x).toLocaleDateString();
        return `
            <div class="bg-card text-text p-1 rounded-lg text-xs flex flex-col items-center border">
                <div class="font-semibold mb-1 border-b border-current w-full text-center pb-1">
                    ${date}
                </div>
                <div>
                    ${val.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                </div>
            </div>
        `;
        }
    },
    dataLabels: { enabled: false }
    };

    const chartEl = document.querySelector(chartSelector);
    if (chartEl && typeof ApexCharts !== 'undefined') {
    if (chartEl._apexChart) {
        chartEl._apexChart.destroy();
    }
    const chart = new ApexCharts(chartEl, options);
    chart.render();
    chartEl._apexChart = chart;
    }

} catch (e) {
    console.error(`Chart für ${apiPath} konnte nicht geladen werden`, e);
}
}

// Hilfsfunktion: alle Charts neu rendern
function refreshAllCharts() {
    // Heizöl
    renderApiChart({
    apiPath: `${API_BASE}/oil`,
    valueKey: "price_eur",
    chartTitle: "Heizölpreis",
    headerSelector: "#oil-header",
    changeSelector: "#oil-change",
    chartSelector: "#oil-chart",
    last: 30,
    });

    // Energy
    renderApiChart({
    apiPath: `${API_BASE}/energy`,
    valueKey: "price_ct_per_kwh",
    chartTitle: "Strompreis",
    headerSelector: "#energy-header",
    changeSelector: "#energy-change",
    chartSelector: "#energy-chart",
    last: 30
    });

    // Petrol, z.B. e5
    renderApiChart({
    apiPath: `${API_BASE}/petrol`,
    valueKey: "e5",
    chartTitle: "Benzinpreis",
    headerSelector: "#petrol-header",
    changeSelector: "#petrol-change",
    chartSelector: "#petrol-chart",
    last: 30
    });

    // Bitcoin-Chart
    renderApiChart({
    apiPath: `${API_BASE}/btc`,
    valueKey: 'price_eur', // wir wandeln die API um
    chartTitle: 'Bitcoin (EUR)',
    headerSelector: '#bitcoin-header',
    changeSelector: '#bitcoin-change',
    chartSelector: '#bitcoin-chart',
    last: 30,
    formatValue: (val) => formatEuro(val, 0), // Funktion ohne Nachkommastellen
    colorUpDown: true
    });
}
refreshAllCharts();

function renderCardResult(svc, data) {
const el = document.getElementById(`card-${svc.id}`);
el.classList.remove('animate-pulse');

// Hilfsfunktion für Punkteanzeige mit Nummern
const renderDots = (instances) => {
    return `<div class="flex flex-wrap space-between gap-3 mt-2 text-sm text-zinc-600 dark:text-zinc-300 text-text">
    ${instances.map((inst, idx) => {
        const color = inst.status === 'green' ? 'bg-green-400' :
                    inst.status === 'yellow' ? 'bg-yellow-500' :
                    'bg-red-500';
        return `
        <div class="flex items-center gap-1" title="${inst.name}">
            <span>${idx+1}.</span>
            ${badgeStatus(inst.status)}
        </div>
        `;
    }).join('')}
    </div>`;
};

    // Karten-Header
    let html = `
    <div class="flex items-center justify-between gap-3">
        <h3 class="font-semibold">${svc.name}</h3>
        ${data.instances ? '' : badgeStatus(data.status)}
    </div>
    `;

// Inhalt je nach Typ
if (data.instances) {
    html += renderDots(data.instances);
} else {
    let statusParts = [];

    if (data.http?.httpStatus != null) {
    statusParts.push(`HTTP: (${data.http.httpStatus})`);
    }

    if (data.tcp?.ms != null) {
    statusParts.push(`Delay: (${data.tcp.ms} ms)`);
    }

    html += `
    <div class="mt-2 text-sm">
        ${statusParts.join(' - ')}
    </div>
    `;
}

el.innerHTML = html;
}

function renderCardError(svc, err, ms) {
const el = document.getElementById(`card-${svc.id}`);
el.classList.remove('animate-pulse');
el.innerHTML = `
    <div class="flex items-center justify-between gap-3">
    <h3 class="font-semibold">${svc.name}</h3>
    ${badge(false)}
    </div>
    <p class="mt-2 text-sm text-red-700 dark:text-red-300">${(err && err.message) || 'Fehler beim Abruf.'}</p>
    <div class="mt-2 text-xs text-zinc-500 dark:text-zinc-400">${svc.url}</div>
    <div class="mt-3 text-xs text-zinc-600 dark:text-zinc-400">${typeof ms === 'number' ? ms + ' ms • ' : ''}Request fehlgeschlagen</div>
`;
}

// Initial Skeletons
// for (const svc of SERVICES) grid.appendChild(cardSkeleton(svc));

// Optional: Tab-Wechsel überwachen und alle Fetches abbrechen
let activeController = null;
document.addEventListener('visibilitychange', () => {
if (document.hidden && activeController) {
    activeController.abort();
}
});
// refreshAll();
// setInterval(refreshAll, 60000);
// setInterval(renderHeizoelChart, 60000);

(() => {
const toggle = document.getElementById('theme-toggle');
const headerFavicon = document.getElementById('header-favicon');

// SVGs for light/dark mode
const moonSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text)]/90 lucide lucide-moon-icon lucide-moon"><path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"/></svg>`;
const sunSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text)]/90 lucide lucide-sun-icon lucide-sun"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`;

const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
let isDark = savedTheme ? savedTheme === 'dark' : prefersDark;

document.documentElement.classList.toggle('dark', isDark);

const updateFavicon = () => {
    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    link.type = 'image/png';
    link.sizes = '32x32';
    document.head.appendChild(link);
    }

    const src = isDark
    ? 'assets/img/favicon/dark-32.png'
    : 'assets/img/favicon/light-32.png';

    // Head-Favicon
    link.href = src;

    // Header-Favicon
    if (headerFavicon) headerFavicon.src = src;
};

const updateUI = () => {
    toggle.innerHTML = isDark ? sunSVG : moonSVG;
    updateFavicon();
};

toggle.addEventListener('click', () => {
    isDark = !isDark;
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    refreshAllCharts();
    updateUI();
});

updateUI();
})();