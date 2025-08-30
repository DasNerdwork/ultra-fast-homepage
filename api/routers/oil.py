from fastapi import APIRouter, Query
from typing import Optional
from api.utils.oil_fetch import fetch_heizoel_price

router = APIRouter(tags=["Oil"])

@router.get("", summary="Get average daily heating oil prices for the last X days")
def get_heizoel_price(
    last: int = Query(
        30,
        ge=1,
        le=90,
        title="Last X days",
        description="Anzahl der letzten Tage, für die die Heizölpreise abgefragt werden.",
        example=7
    )
):
    return fetch_heizoel_price(last)
