from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import date
import os
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

router = APIRouter(tags=["ETFs"])

class DailyETFPrice(BaseModel):
    date: date
    price_eur: float

def get_conn():
    return psycopg2.connect(DB_URL)

def fetch_prices(table_name: str, last: Optional[int]):
    conn = get_conn()
    cur = conn.cursor()

    query = f"SELECT date, price_eur FROM {table_name}"
    params = []

    if last is not None:
        query += " ORDER BY date DESC LIMIT %s"
        params.append(last)
    else:
        query += " ORDER BY date ASC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Bei last angegeben, aufsteigend sortieren
    if last is not None:
        rows = list(reversed(rows))

    return [
        DailyETFPrice(date=r[0], price_eur=float(r[1]))
        for r in rows
    ]

# ------------------------------
# Endpoints für die drei ETFs
# ------------------------------

@router.get("/spdr", response_model=List[DailyETFPrice], summary="SPDR MSCI World (Acc) Preise")
def get_spdr_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("spdr_prices_daily", last)

@router.get("/vaneck", response_model=List[DailyETFPrice], summary="VanEck Semiconductor (Acc) Preise")
def get_vaneck_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("vaneck_prices_daily", last)

@router.get("/xtrackers", response_model=List[DailyETFPrice], summary="Xtrackers MSCI World (Acc) Preise")
def get_xtrackers_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("xtrackers_prices_daily", last)
