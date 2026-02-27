from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from backend.runtime_settings import get_pagespeed_api_key, save_settings

router = APIRouter()


class SettingsReadResponse(BaseModel):
    pagespeed_api_key_present: bool
    pagespeed_api_key_preview: str | None = None


class SettingsUpdateRequest(BaseModel):
    pagespeed_api_key: str | None = None

    @field_validator("pagespeed_api_key")
    @classmethod
    def normalize_pagespeed_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


def _preview_key(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}***{value[-3:]}"


@router.get("", response_model=SettingsReadResponse)
async def read_settings() -> SettingsReadResponse:
    key = get_pagespeed_api_key()
    return SettingsReadResponse(
        pagespeed_api_key_present=bool(key),
        pagespeed_api_key_preview=_preview_key(key),
    )


@router.post("", response_model=SettingsReadResponse)
async def update_settings(payload: SettingsUpdateRequest) -> SettingsReadResponse:
    stored = save_settings(pagespeed_api_key=payload.pagespeed_api_key)
    key = stored.get("pagespeed_api_key")
    if not isinstance(key, str):
        key = None
    return SettingsReadResponse(
        pagespeed_api_key_present=bool(key),
        pagespeed_api_key_preview=_preview_key(key),
    )
