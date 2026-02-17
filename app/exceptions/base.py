from fastapi import status


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UserAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__("Email already registered", status.HTTP_409_CONFLICT)


class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__("Invalid credentials", status.HTTP_401_UNAUTHORIZED)


class InvalidCodeError(AppException):
    def __init__(self, reason: str = "Invalid or expired code") -> None:
        super().__init__(reason, status.HTTP_422_UNPROCESSABLE_ENTITY)


class UserAlreadyActiveError(AppException):
    def __init__(self) -> None:
        super().__init__("Account is already active", status.HTTP_409_CONFLICT)
