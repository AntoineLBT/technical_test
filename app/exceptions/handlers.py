from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException, InvalidCredentialsError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        headers = {}
        if isinstance(exc, InvalidCredentialsError):
            headers["WWW-Authenticate"] = "Basic"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
            headers=headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic v2 stores the original Exception object in error['ctx']['error'],
        # which is not JSON serializable — convert it to string.
        errors = []
        for error in exc.errors():
            err = dict(error)
            if "ctx" in err:
                err["ctx"] = {
                    k: str(v) if isinstance(v, Exception) else v
                    for k, v in err["ctx"].items()
                }
            errors.append(err)
        return JSONResponse(status_code=422, content={"detail": errors})
