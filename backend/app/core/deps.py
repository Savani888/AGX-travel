from fastapi import Depends, Request
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.errors import AppException, ErrorCode
from app.core.security import decode_access_token, oauth2_scheme
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.user_repository import UserRepository


def get_db() -> Session:
    yield from get_db_session()


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise AppException(
            code=ErrorCode.AUTH_ERROR,
            message="Invalid token",
            status_code=401,
        ) from exc

    user_id = payload.get("sub")
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AppException(
            code=ErrorCode.AUTH_ERROR,
            message="User not found for token",
            status_code=401,
        )
    request.state.user_id = user.id
    return user
