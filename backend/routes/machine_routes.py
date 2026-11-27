import os
import json
import redis

from fastapi import APIRouter, HTTPException
from backend.services.machine_service import get_machine_history

router = APIRouter()

cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)


@router.get("/live")
def live_machines():

    try:
        keys = cache.keys("machine:*:latest")

        machines = []

        for key in keys:
            value = cache.get(key)

            if value:
                machines.append(json.loads(value))

        return {
            "total_machines": len(machines),
            "machines": machines
        }

    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get("/{machine_id}/history")
def machine_history(machine_id: str):

    try:
        history = get_machine_history(machine_id)

        return {"history": history}

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))