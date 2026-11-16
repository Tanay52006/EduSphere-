from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.models.auth import User
from app.schemas.auth import ProfileResponse, ProfileUpdate

router = APIRouter(tags=["profile"])


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> ProfileResponse:  # noqa: B008
    profile = user.profile
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value.model_dump() if hasattr(value, "model_dump") else value)
    db.commit()
    db.refresh(profile)
    return ProfileResponse.model_validate(profile)
