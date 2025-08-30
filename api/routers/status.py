from fastapi import APIRouter, Query
from typing import Optional
from api.utils.status_check import get_service_status

router = APIRouter(tags=["Status"])

@router.get("", summary="Get status of services and applications running on DasNerdwork.net")
def status(
    service: Optional[str] = Query(
        None,
        title="Service Name",
        description="Name des Services, dessen Status abgefragt werden soll. Wenn leer, alle Services."
    )
):
    return get_service_status(service)
