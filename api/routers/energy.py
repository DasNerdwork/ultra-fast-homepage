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

router = APIRouter(tags=["Energy"])

class DailyEnergyPrice(BaseModel):
    date: date
    price_ct_per_kwh: float

def get_conn():
    return psycopg2.connect(DB_URL)

@router.get("", response_model=List[DailyEnergyPrice], summary="Get daily average energy prices")
def get_energy_prices(
    last: Optional[int] = Query(
        None,
        ge=1,
        le=90,
        description="Number of most recent days (max 90)",
        example=7
    )
):
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT date, price_ct_per_kwh FROM energy_prices_daily"
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

    # if limited, reverse to chronological order
    if last is not None:
        rows = list(reversed(rows))

    return [
        DailyEnergyPrice(
            date=r[0],
            price_ct_per_kwh=float(r[1])
        )
        for r in rows
    ]
