from sqlalchemy.orm import Session

from app.core.errors import AppException, ErrorCode
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.api.contracts import LoginRequest, TokenResponse, UserRegisterRequest, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def register(self, req: UserRegisterRequest) -> UserResponse:
        if self.users.get_by_email(req.email):
            raise AppException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Email already registered",
                status_code=409,
            )
        user = User(email=req.email, hashed_password=hash_password(req.password), full_name=req.full_name)
        created = self.users.create(user)
        return UserResponse(id=created.id, email=created.email, full_name=created.full_name, preferences=created.preferences)

    def login(self, req: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise AppException(code=ErrorCode.AUTH_ERROR, message="Invalid credentials", status_code=401)
        return TokenResponse(access_token=create_access_token(user.id))
