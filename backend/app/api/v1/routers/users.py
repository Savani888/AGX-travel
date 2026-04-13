from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.api.contracts import TravelerPreferences, UserResponse
from app.services.traveler_profile_service import TravelerProfileService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return TravelerProfileService(db).me(user)


@router.put("/me/preferences", response_model=UserResponse)
def update_preferences(
    request: TravelerPreferences,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TravelerProfileService(db).update_preferences(user, request)
