from sqlalchemy.orm import Session

from app.core.errors import AppException, ErrorCode
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.api.contracts import TravelerPreferences, UserResponse


class TravelerProfileService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def me(self, user: User) -> UserResponse:
        return UserResponse(id=user.id, email=user.email, full_name=user.full_name, preferences=user.preferences)

    def update_preferences(self, user: User, preferences: TravelerPreferences) -> UserResponse:
        found = self.users.get_by_id(user.id)
        if not found:
            raise AppException(code=ErrorCode.NOT_FOUND, message="User not found", status_code=404)
        updated = self.users.update_preferences(found, preferences.model_dump())
        return UserResponse(id=updated.id, email=updated.email, full_name=updated.full_name, preferences=updated.preferences)
