from app.repositories.users import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError

class AuthUsecase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, email: str, password: str, role: str = "user"):
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError()
        hashed_pw = hash_password(password)
        user = await self.user_repo.create(email, hashed_pw, role)
        return user

    async def login(self, email: str, password: str):
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(data=token_data)
        return access_token

    async def me(self, user_id: int):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user