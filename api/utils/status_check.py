import socket
import time
import requests
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

# .env laden
load_dotenv()
DOMAIN = os.getenv("DOMAIN")
HA_TOKEN = os.getenv("HA_TOKEN")

# Services definieren
# port  -> TCP-Check gegen localhost ("läuft der Prozess?")
# url   -> HTTP-Check über die Domain/nginx ("funktioniert der Weg von außen?")
# Hinweis: Dienste, die auf 127.0.0.1 gebunden sind (musikbot, voidwatch,
# pihole, netdata), sind von außen bewusst nicht mehr erreichbar. Der
# TCP-Check läuft deshalb lokal, der HTTP-Check weiterhin über nginx.
SERVICES = {
    'teamspeak': {'port': 30033, 'url': None},
    'musikbot': {'port': 8087, 'url': f"https://musik.{DOMAIN}/health"},
    'clashscout': {'port': None, 'url': "https://clashscout.com/health"},
    'voidwatch': {'port': 8090, 'url': f"https://voidwatch.{DOMAIN}/health"},
    'nextcloud': {'port': None, 'url': f"https://cloud.{DOMAIN}/health"},
    'unifi': {'port': 8443, 'url': f"https://unifi.{DOMAIN}/health"},
    'homeassistant': {'port': 8123, 'url': f"https://home.{DOMAIN}/health"},
    'pihole': {'port': 88, 'url': f"https://pi.{DOMAIN}/health"},
    'netdata': {'port': 19999, 'url': f"https://data.{DOMAIN}/health"},
    'satisfactory': {'port': 15777, 'url': None},
    'gmod': {'port': 27015, 'url': None},
    'mc-vanilla': {'port': 25565, 'url': None},
    'mc-modpack': {'port': 25566, 'url': None},
    'pb-smetti': {'port': 25000, 'url': f"https://smetti.{DOMAIN}/health"},
    'pb-junky': {'port': 25001, 'url': f"https://junky.{DOMAIN}/health"},
    'pb-orphi': {'port': 25002, 'url': f"https://orphi.{DOMAIN}/health"},
    'pb-snacky': {'port': 25003, 'url': f"https://snacky.{DOMAIN}/health"},
}

# Cache für den Full-Status (in Sekunden)
CACHE_TTL = 30
_status_cache = {"ts": 0.0, "data": None}


def check_tcp(host: str, port: Optional[int], timeout=2):
    if port is None:
        return None
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout):
            ms = max(1, int((time.time() - start) * 1000))
            return {'ok': True, 'ms': ms}
    except OSError:
        return {'ok': False, 'ms': None}


def check_http(url: Optional[str], headers=None, timeout=2, method="HEAD"):
    if url is None:
        return None
    try:
        if method == "HEAD":
            resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        else:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        return {'ok': 200 <= resp.status_code < 400, 'httpStatus': resp.status_code}
    except requests.RequestException:
        return {'ok': False, 'httpStatus': None}


def evaluate_status(http_res: Optional[dict], tcp_res: Optional[dict]) -> str:
    """Bewertet die Check-Ergebnisse.

    green  = alle durchgeführten Checks ok
    yellow = mindestens ein Check ok, mindestens einer fehlgeschlagen
    red    = alle durchgeführten Checks fehlgeschlagen (oder keiner definiert)
    """
    http_ok = http_res['ok'] if http_res is not None else None
    tcp_ok = tcp_res['ok'] if tcp_res is not None else None
    checks = [c for c in (http_ok, tcp_ok) if c is not None]
    if not checks or all(c is False for c in checks):
        return 'red'
    if all(checks):
        return 'green'
    return 'yellow'


def group_services(results: dict, prefix: str, label_map: Optional[dict] = None):
    if label_map is None:
        label_map = {}
    group = {'instances': [], 'status': 'green'}
    for id, res in results.items():
        if id.startswith(prefix):
            name = label_map.get(id, id.replace(f"{prefix}-", "").capitalize())
            group['instances'].append({'name': name, 'status': res['status']})
    statuses = [i['status'] for i in group['instances']]
    if statuses and all(s == 'green' for s in statuses):
        group['status'] = 'green'
    elif all(s == 'red' for s in statuses) and statuses:
        group['status'] = 'red'
    else:
        group['status'] = 'yellow'
    return group


def _check_one(item):
    """Führt HTTP- und TCP-Check für einen einzelnen Service aus."""
    id, svc = item
    headers = {"Authorization": f"Bearer {HA_TOKEN}"} if id == "homeassistant" else None
    http_res = check_http(svc['url'], headers=headers, method="GET" if id == "homeassistant" else "HEAD")
    # TCP-Check lokal: misst, ob der Dienst auf dem Server läuft
    tcp_res = check_tcp("127.0.0.1", svc['port'])
    return id, {
        'http': http_res,
        'tcp': tcp_res,
        'status': evaluate_status(http_res, tcp_res),
    }


def get_service_status(service_name: Optional[str] = None):
    now = time.time()

    # Cache nur für den Full-Check (alle Services) nutzen
    if service_name is None and _status_cache["data"] is not None and now - _status_cache["ts"] < CACHE_TTL:
        return _status_cache["data"]

    items = [
        (id, svc) for id, svc in SERVICES.items()
        if not service_name
        or service_name == id
        or (service_name.startswith("pb") and id.startswith("pb"))
    ]

    # Checks parallel ausführen
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(ex.map(_check_one, items))

    if service_name is None:
        _status_cache["ts"] = now
        _status_cache["data"] = results

    return results