import logging
import sys
import time
import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool

from product_evaluator.config import settings

# Type variables for function decorator typing
F = TypeVar("F", bound=Callable[..., Any])

# Create logger
logger = logging.getLogger("product_evaluator")


def get_request_id(request: Optional[Request] = None) -> str:
    """Get a unique ID for the current request, or generate one if none exists."""
    if request and hasattr(request.state, "id"):
        return cast(str, request.state.id)
    return f"req-{time.time_ns()}"


def log_info(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message with optional extra details."""
    _extra = extra or {}
    logger.info(message, extra=_extra)


def log_error(message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
    """Log an error message with optional extra details and exception info."""
    _extra = extra or {}
    logger.error(message, extra=_extra, exc_info=exc_info)


def log_warning(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message with optional extra details."""
    _extra = extra or {}
    logger.warning(message, extra=_extra)


def log_debug(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """Log a debug message with optional extra details."""
    _extra = extra or {}
    logger.debug(message, extra=_extra)


def log_critical(message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
    """Log a critical message with optional extra details and exception info."""
    _extra = extra or {}
    logger.critical(message, extra=_extra, exc_info=exc_info)


def log_request_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware function to log HTTP requests and responses."""
    start_time = time.time()
    request_id = get_request_id(request)
    request.state.id = request_id
    
    log_info(
        f"Request started: {request.method} {request.url.path}",
        {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "params": dict(request.query_params),
        },
    )
    
    try:
        response = call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        log_info(
            f"Request completed: {request.method} {request.url.path}",
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time": process_time,
            },
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_error(
            f"Request failed: {request.method} {request.url.path}",
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "processing_time": process_time,
            },
            exc_info=True,
        )
        raise


def log_execution_time(func: F) -> F:
    """Decorator to log the execution time of a function."""
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_debug(
                f"Function executed: {func.__name__}",
                {"function": func.__name__, "execution_time": execution_time},
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_error(
                f"Function failed: {func.__name__}",
                {
                    "function": func.__name__,
                    "error": str(e),
                    "execution_time": execution_time,
                },
                exc_info=True,
            )
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_debug(
                f"Function executed: {func.__name__}",
                {"function": func.__name__, "execution_time": execution_time},
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_error(
                f"Function failed: {func.__name__}",
                {
                    "function": func.__name__,
                    "error": str(e),
                    "execution_time": execution_time,
                },
                exc_info=True,
            )
            raise

    return cast(F, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)


# Initialize logging format for console output if running directly
if __name__ == "__main__":
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelName(settings.LOG_LEVEL.upper()))