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

router = APIRouter(tags=["Bitcoin"])

class DailyBTCPrice(BaseModel):
    date: date
    price_eur: float

def get_conn():
    return psycopg2.connect(DB_URL)

@router.get("", response_model=List[DailyBTCPrice], summary="Get BTC prices for the last X days")
def get_daily_btc_prices(
    last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)
):
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT date, price_eur FROM btc_prices_daily"
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

    # Wenn 'last' angegeben war, sortiere aufsteigend
    if last is not None:
        rows = list(reversed(rows))

    return [
        DailyBTCPrice(
            date=r[0],
            price_eur=float(r[1])
        )
        for r in rows
    ]
