from fastapi import APIRouter, Query
from datetime import date, timedelta
from typing import Optional, List
from api.utils.energy_fetch import fetch_energycharts_daily
from pydantic import BaseModel

router = APIRouter(tags=["Energy"])

class EnergyPrice(BaseModel):
    date: date
    price: float

@router.get("", response_model=List[EnergyPrice], summary="Get average daily energy prices for the last X days")
async def get_energy_prices(
    last: int = Query(
        7,
        title="Number of days",
        description="Number of most recent days to fetch average energy prices for.",
        ge=1,
        le=90,
        examples=[1, 7, 30, 90],
        deprecated=False,
        json_schema_extra={
            "defaultExplanation": "If not provided, defaults to 7 days."
        }
    )
):
    today = date.today()
    start = today - timedelta(days=last)

    df = fetch_energycharts_daily(start.isoformat(), today.isoformat())

    df = df.tail(last)

    return df.to_dict(orient="records")
