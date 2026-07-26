from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from api.db import get_cursor

router = APIRouter(tags=["ETFs"])

class DailyETFPrice(BaseModel):
    date: date
    price_eur: float

# Whitelist: Endpoint-Name -> Tabellenname
ETF_TABLES = {
    "spdr": "spdr_prices_daily",
    "vaneck": "vaneck_prices_daily",
    "xtrackers": "xtrackers_prices_daily",
}

def fetch_prices(etf: str, last: Optional[int]):
    table_name = ETF_TABLES[etf]

    query = f"SELECT date, price_eur FROM {table_name}"
    params = []

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

    return [DailyETFPrice(date=r[0], price_eur=float(r[1])) for r in rows]

# ------------------------------
# Endpoints für die drei ETFs
# ------------------------------

@router.get("/spdr", response_model=List[DailyETFPrice], summary="SPDR MSCI World (Acc) Preise")
def get_spdr_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("spdr", last)

@router.get("/vaneck", response_model=List[DailyETFPrice], summary="VanEck Semiconductor (Acc) Preise")
def get_vaneck_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("vaneck", last)

@router.get("/xtrackers", response_model=List[DailyETFPrice], summary="Xtrackers MSCI World (Acc) Preise")
def get_xtrackers_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("xtrackers", last)