import os
import time
import requests
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from api.db import get_cursor

STATION_ID = os.getenv("TANKERKOENIG_STATION_ID")
API_KEY = os.getenv("TANKERKOENIG_API_KEY")

router = APIRouter(tags=["Petrol"])

# ----------------------
# Schemas
# ----------------------
class DailyPetrolPrice(BaseModel):
    date: date
    price: float
    price_high: Optional[float] = None

class CurrentPetrolPrices(BaseModel):
    e5: Optional[float] = None
    e10: Optional[float] = None
    diesel: Optional[float] = None
    is_open: bool
    fetched_at: int

# Whitelist: erlaubte Spalten
FUEL_COLUMNS = {"e5", "e10", "diesel"}

# Cache für den Live-Preis, damit nicht jeder Seitenaufruf einen
# Tankerkönig-Call auslöst (schützt API-Key-Quota und Rate-Limit)
LIVE_TTL = 900  # 15 Minuten
_live_cache = {"ts": 0.0, "data": None}

# ----------------------
# Historische Preise (aus DB)
# ----------------------
def fetch_prices(column: str, last: Optional[int]):
    if column not in FUEL_COLUMNS:
        raise ValueError(f"Unknown fuel type: {column}")

    query = f"SELECT date, {column}, {column}_high FROM daily_prices WHERE station_id = %s"
    params = [STATION_ID]

    if last is not None:
        query += " ORDER BY date DESC LIMIT %s"
        params.append(last)
    else:
        query += " ORDER BY date ASC"

    with get_cursor() as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

    if last is not None:
        rows = list(reversed(rows))

    return [
        {
            "date": r[0],
            "price": float(r[1]),
            "price_high": float(r[2]) if r[2] is not None else None,
        }
        for r in rows if r[1] is not None
    ]

# ----------------------
# Endpoints
# ----------------------
@router.get("/current", response_model=CurrentPetrolPrices, summary="Aktuelle Preise (live, 15min Server-Cache)")
def get_current_prices():
    now = time.time()
    if _live_cache["data"] is not None and now - _live_cache["ts"] < LIVE_TTL:
        return _live_cache["data"]

    url = f"https://creativecommons.tankerkoenig.de/json/detail.php?id={STATION_ID}&apikey={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        station = resp.json().get("station", {})
    except requests.RequestException:
        # Tankerkönig nicht erreichbar: alten Cache-Wert liefern falls
        # vorhanden (besser stale als gar nichts), sonst 503
        if _live_cache["data"] is not None:
            return _live_cache["data"]
        raise HTTPException(status_code=503, detail="Preisdaten aktuell nicht verfügbar")

    result = CurrentPetrolPrices(
        e5=station.get("e5"),
        e10=station.get("e10"),
        diesel=station.get("diesel"),
        is_open=station.get("isOpen", False),
        fetched_at=int(now),
    )
    _live_cache["ts"] = now
    _live_cache["data"] = result
    return result

@router.get("/e5", response_model=List[DailyPetrolPrice], summary="E5 Preise")
def get_e5_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("e5", last)

@router.get("/e10", response_model=List[DailyPetrolPrice], summary="E10 Preise")
def get_e10_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("e10", last)

@router.get("/diesel", response_model=List[DailyPetrolPrice], summary="Diesel Preise")
def get_diesel_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("diesel", last)