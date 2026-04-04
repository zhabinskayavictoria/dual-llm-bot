from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.usecases.auth import AuthUsecase
from app.core.security import decode_token
from app.core.exceptions import InvalidTokenError
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_auth_uc(repo: UserRepository = Depends(get_user_repo)) -> AuthUsecase:
    return AuthUsecase(repo)

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise InvalidTokenError()
        return int(user_id)
    except JWTError:
        raise InvalidTokenError()