import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class UserStub:
    def __init__(self, id: uuid.UUID):
        self.id = id

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserStub:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return UserStub(id=uuid.UUID(user_id))
    except (JWTError, ValueError):
        raise credentials_exception
