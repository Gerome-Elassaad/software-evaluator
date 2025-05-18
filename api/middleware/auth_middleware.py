from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

import jwt
from jwt.exceptions import PyJWTError

from product_evaluator.config import settings
from product_evaluator.utils.logger import log_info, log_error


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks for valid JWT token in Authorization header for protected routes.
    
    This middleware doesn't verify the token's payload or user existence, it only ensures
    that a valid JWT token is present for routes that should be protected. The detailed
    user verification is handled by the route dependencies.
    
    Public routes (like /docs, /auth/token, /auth/register) bypass this check.
    """
    
    def __init__(self, app):
        """Initialize the middleware."""
        super().__init__(app)
        # Define paths that don't require authentication
        self.public_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/token",
            "/api/auth/register",
            "/",
            "/static",
            "/favicon.ico",
        ]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request."""
        # Check if the path is public
        path = request.url.path
        if self._is_public_path(path):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token format
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token format"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Perform basic token validation (structure and signature)
        try:
            # Just decode to verify signature, not checking payload details here
            jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
        except PyJWTError as e:
            log_error(f"JWT validation error in middleware: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Token is valid at a basic level, continue to the endpoint
        # The endpoint's dependency will perform full validation
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if a path is public (doesn't require authentication).
        
        Args:
            path: The request path
            
        Returns:
            True if public, False otherwise
        """
        # Check if the path exactly matches a public path
        if path in self.public_paths:
            return True
        
        # Check if the path starts with a public path prefix
        for public_path in self.public_paths:
            if path.startswith(public_path + "/"):
                return True
        
        return False