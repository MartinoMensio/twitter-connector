from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import UrlStr

from ..service import entity_manager
from ..model import classes

router = APIRouter()
