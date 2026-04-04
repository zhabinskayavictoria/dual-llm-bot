from fastapi import HTTPException, status

class AppHTTPException(HTTPException):
    pass

class UserAlreadyExistsError(AppHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

class InvalidCredentialsError(AppHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

class InvalidTokenError(AppHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

class UserNotFoundError(AppHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")