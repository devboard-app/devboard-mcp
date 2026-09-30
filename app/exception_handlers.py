import functools
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from mcp.server.mcpserver.exceptions import ToolError

from app.exceptions import (
    ForbiddenException,
    InvalidRequestException,
    MissingTokenException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(MissingTokenException)
    async def missing_token_handler(request, exc):
        return JSONResponse(
            status_code=401, content={"detail": "Missing bearer token", "errors": None}
        )

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request, exc):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired token", "errors": None},
        )

    @app.exception_handler(ForbiddenException)
    async def forbidden_handler(request, exc):
        return JSONResponse(
            status_code=403, content={"detail": "Forbidden", "errors": None}
        )

    @app.exception_handler(NotFoundException)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404, content={"detail": "Not found", "errors": None}
        )

    @app.exception_handler(InvalidRequestException)
    async def invalid_request_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc) or "Invalid request", "errors": None},
        )

    @app.exception_handler(ServiceUnavailableException)
    async def service_unavailable_handler(request, exc):
        return JSONResponse(
            status_code=502,
            content={"detail": "Work service is not working", "errors": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc):
        errors: dict[str, list[str]] = {}
        for error in exc.errors():
            field_parts = [str(p) for p in error["loc"] if not isinstance(p, int)]
            field = field_parts[-1] if field_parts else "non_field_errors"
            errors.setdefault(field, []).append(error["msg"])
        if not errors:
            return JSONResponse(
                status_code=422,
                content={"detail": "Validation failed", "errors": errors},
            )
        return JSONResponse(
            status_code=422,
            content={"detail": next(iter(errors.values()))[0], "errors": errors},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail, "errors": None}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Unexpected error occurred", "errors": None},
        )


TOOL_ERROR_MESSAGES = {
    MissingTokenException: "Missing bearer token. Log in to DevBoard and reconnect.",
    UnauthorizedException: "DevBoard rejected the token (expired or invalid). Log in again.",
    ForbiddenException: "You don't have permission to do this in DevBoard.",
    NotFoundException: "Not found in DevBoard.",
    InvalidRequestException: "DevBoard rejected the request.",
    ServiceUnavailableException: "The DevBoard work service is not reachable.",
}


def tool_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except tuple(TOOL_ERROR_MESSAGES) as exc:
            raise ToolError(str(exc) or TOOL_ERROR_MESSAGES[type(exc)]) from exc

    return wrapper
