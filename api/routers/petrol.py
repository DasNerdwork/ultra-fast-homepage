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
STATION_ID = os.getenv("TANKERKOENIG_STATION_ID")

router = APIRouter(tags=["Petrol"])

class DailyPrice(BaseModel):
    date: date
    e5: Optional[float] = None
    e10: Optional[float] = None
    diesel: Optional[float] = None

def get_conn():
    return psycopg2.connect(DB_URL)

@router.get("", response_model=List[DailyPrice], summary="Get average daily petrol (e5, e10, diesel) prices for the last X days")
def get_daily_prices(
    last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)
):
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT date, e5, e10, diesel FROM daily_prices WHERE station_id = %s"
    params = [STATION_ID]

    if last is not None:
        query += " ORDER BY date DESC LIMIT %s"
        params.append(last)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Wenn 'last' angegeben war, sortiere rückwärts wieder aufsteigend für die API
    if last is not None:
        rows = list(reversed(rows))

    return [
        DailyPrice(
            date=r[0],
            e5=float(r[1]) if r[1] is not None else None,
            e10=float(r[2]) if r[2] is not None else None,
            diesel=float(r[3]) if r[3] is not None else None
        )
        for r in rows
    ]
