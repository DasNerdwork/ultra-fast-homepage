import socket
import requests
from typing import Optional
import os
from dotenv import load_dotenv

# .env laden
load_dotenv()
DOMAIN = os.getenv("DOMAIN")
HA_TOKEN = os.getenv("HA_TOKEN")

# Services definieren
SERVICES = {
    'teamspeak': {'port': 10011, 'url': None},
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
    'pb-smetti': {'port': 25000, 'url': f"https://smetti.{DOMAIN}/health"},
    'pb-junky': {'port': 25001, 'url': f"https://junky.{DOMAIN}/health"},
    'pb-orphi': {'port': 25002, 'url': f"https://orphi.{DOMAIN}/health"},
    'pb-snacky': {'port': 25003, 'url': f"https://snacky.{DOMAIN}/health"},
}

def check_tcp(host: str, port: Optional[int], timeout=2):
    if port is None:
        return None
    try:
        import time
        start = time.time()
        with socket.create_connection((host, port), timeout):
            ms = max(1, int((time.time() - start) * 1000))
            return {'ok': True, 'ms': ms}
    except:
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
    except:
        return {'ok': False, 'httpStatus': None}


def group_services(results: dict, prefix: str, label_map: Optional[dict] = None):
    if label_map is None:
        label_map = {}
    group = {'instances': [], 'status': 'green'}
    for id, res in results.items():
        if id.startswith(prefix):
            name = label_map.get(id, id.replace(f"{prefix}-", "").capitalize())
            group['instances'].append({'name': name, 'status': res['status']})
    statuses = [i['status'] for i in group['instances']]
    if all(s == 'green' for s in statuses):
        group['status'] = 'green'
    elif 'red' in statuses:
        group['status'] = 'yellow'
    else:
        group['status'] = 'yellow'
    return group

def get_service_status(service_name: Optional[str] = None):
    results = {}
    for id, svc in SERVICES.items():
        if service_name and service_name != id and not (service_name.startswith("pb") and id.startswith("pb")):
            continue
        headers = {"Authorization": f"Bearer {HA_TOKEN}"} if id == "homeassistant" else None
        http_res = check_http(svc['url'], headers=headers, method="GET" if id=="homeassistant" else "HEAD")
        tcp_res = check_tcp(DOMAIN, svc['port'])
        status = 'green'
        if ((http_res is False or http_res is None) and (tcp_res is False or tcp_res is None)):
            status = 'red'
        elif (http_res is False or tcp_res is False):
            status = 'yellow'
        results[id] = {'http': http_res, 'tcp': tcp_res, 'status': status}

    return results

