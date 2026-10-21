from fastapi import APIRouter
from pydantic import BaseModel

from ..deps import SettingsDep

router = APIRouter(tags=["meta"])


class AppConfig(BaseModel):
    currency: str


@router.get("/config", response_model=AppConfig)
def app_config(settings: SettingsDep) -> AppConfig:
    """Display settings the frontend needs."""
    return AppConfig(currency=settings.currency.upper())
