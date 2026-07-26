from fastapi import APIRouter, Query
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from api.db import get_cursor

router = APIRouter(tags=["Bitcoin"])

class DailyBTCPrice(BaseModel):
    date: date
    price_eur: float

@router.get("", response_model=List[DailyBTCPrice], summary="Get BTC prices for the last X days")
def get_daily_btc_prices(
    last: Optional[int] = Query(None, ge=1, le=90, description="Letzte X Einträge", example=7)
):
    query = "SELECT date, price_eur FROM btc_prices_daily"
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

    return [DailyBTCPrice(date=r[0], price_eur=float(r[1])) for r in rows]