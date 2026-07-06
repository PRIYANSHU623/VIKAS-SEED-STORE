"""
Global Exception Handlers
Provides production-safe error responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.config import ENVIRONMENT

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API errors"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "INVALID_REQUEST",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ResourceNotFound(APIException):
    """Raised when a requested resource is not found"""
    def __init__(self, message: str = "Resource not found", resource_type: str = ""):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type} if resource_type else {}
        )


class ValidationError(APIException):
    """Raised when validation fails"""
    def __init__(self, message: str = "Validation failed", field: str = ""):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class UnauthorizedError(APIException):
    """Raised when user is not authenticated"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(APIException):
    """Raised when user doesn't have permission"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class RateLimitError(APIException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class DatabaseError(APIException):
    """Raised when database operation fails"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )


def create_error_response(
    message: str,
    status_code: int,
    error_code: str = "ERROR",
    details: dict = None,
    request_id: str = None
) -> dict:
    """
    Create a standardized error response
    In production, don't expose technical details
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if ENVIRONMENT == "development" and details:
        response["error"]["details"] = details
    
    if request_id:
        response["request_id"] = request_id
    
    return response


async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    logger.warning(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details,
            request_id=request_id
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    error_code = "HTTP_ERROR"
    if exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=str(exc.detail),
            status_code=exc.status_code,
            error_code=error_code,
            request_id=request_id
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        f"Validation Error: {len(exc.errors())} error(s)",
        extra={
            "path": request.url.path,
            "errors": exc.errors() if ENVIRONMENT == "development" else "See logs"
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    # Extract first error for user message
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = first_error.get("loc", ["unknown"])[1] if len(first_error.get("loc", [])) > 1 else "unknown"
    
    details = {}
    if ENVIRONMENT == "development":
        details = {
            "validation_errors": [
                {
                    "field": str(e.get("loc", [])),
                    "message": e.get("msg"),
                    "type": e.get("type")
                }
                for e in errors
            ]
        }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            message=f"Validation failed for field: {field}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=request_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}",
        extra={
            "path": request.url.path,
            "exception": str(exc) if ENVIRONMENT == "development" else "Internal error"
        },
        exc_info=True
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    # Never expose internal exception details to users
    message = "An unexpected error occurred"
    if ENVIRONMENT == "development":
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            request_id=request_id
        )
    )
