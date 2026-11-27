from fastapi import APIRouter, HTTPException

from backend.services.analytics_service import get_machine_summary

router = APIRouter()


@router.get("/summary")
def machine_summary():

    try:
        return get_machine_summary()

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))