from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.analytics.wrapper import track
from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.models.auth import User
from app.schemas.auth import OnboardingComplete, ProfileResponse

router = APIRouter(tags=["onboarding"])


@router.post("/onboarding/complete", response_model=ProfileResponse)
def complete_onboarding(payload: OnboardingComplete, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> ProfileResponse:  # noqa: B008
    user.profile.path_preference = payload.path_choice
    user.profile.onboarding_completed = True
    db.commit()
    db.refresh(user.profile)
    track("Onboarding Completed", {"user_id": user.id, "path_choice": payload.path_choice})
    return ProfileResponse.model_validate(user.profile)
