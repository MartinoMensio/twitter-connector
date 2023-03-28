from typing import List
from fastapi import APIRouter, HTTPException

from ..service import entity_manager, persistence
from ..model import classes

router = APIRouter()


@router.get("/status")
def get_status():
    # test db
    try:
        mongo_ok = persistence.ping_db()["ok"]
        mongo_status = "ok" if mongo_ok == 1.0 else "error"
    except:
        mongo_status = "exception"

    # how is the API dealing with things?
    api_ok = entity_manager.api.alive
    api_status = "ok" if api_ok else "error"

    # overall
    if mongo_status == "ok" and api_status == "ok":
        status = "ok"
    else:
        status = "error"

    return {
        "status": status,
        "details": {"mongo_status": mongo_status, "api_status": api_status},
    }
