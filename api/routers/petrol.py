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

# ----------------------
# Schemas
# ----------------------
class DailyE5Price(BaseModel):
    date: date
    price: float

class DailyE10Price(BaseModel):
    date: date
    price: float

class DailyDieselPrice(BaseModel):
    date: date
    price: float

# ----------------------
# DB Connection Helper
# ----------------------
def get_conn():
    return psycopg2.connect(DB_URL)

def fetch_prices(column: str, last: Optional[int]):
    conn = get_conn()
    cur = conn.cursor()
    
    query = f"SELECT date, {column} FROM daily_prices WHERE station_id = %s"
    params = [STATION_ID]

    if last is not None:
        query += " ORDER BY date DESC LIMIT %s"
        params.append(last)
    else:
        query += " ORDER BY date ASC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Rückwärts sortieren, falls 'last' angegeben
    if last is not None:
        rows = list(reversed(rows))

    return [{"date": r[0], "price": float(r[1])} for r in rows if r[1] is not None]

# ----------------------
# Endpoints
# ----------------------
@router.get("/e5", response_model=List[DailyE5Price], summary="E5 Preise")
def get_e5_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("e5", last)

@router.get("/e10", response_model=List[DailyE10Price], summary="E10 Preise")
def get_e10_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("e10", last)

@router.get("/diesel", response_model=List[DailyDieselPrice], summary="Diesel Preise")
def get_diesel_prices(last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)):
    return fetch_prices("diesel", last)
