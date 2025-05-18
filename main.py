import os
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from product_evaluator.config import settings, logger
from product_evaluator.api.middleware.auth_middleware import AuthMiddleware
from product_evaluator.api.routes import user_routes, product_routes, evaluation_routes
from product_evaluator.utils.database import initialize_db
from product_evaluator.utils.logger import log_request_middleware
from product_evaluator.models.evaluation.criteria_model import create_default_criteria


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered product evaluation tool for software developers and founders",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Initialize database and default data
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    
    # Initialize database
    initialize_db()
    
    # Create default criteria
    create_default_criteria()
    
    logger.info(f"{settings.APP_NAME} started successfully")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add authentication middleware
app.add_middleware(AuthMiddleware)


# Add request logging middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Log HTTP requests and responses."""
    return await log_request_middleware(request, call_next)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Include routers
app.include_router(user_routes.router, prefix="/api", tags=["users"])
app.include_router(product_routes.router, prefix="/api", tags=["products"])
app.include_router(evaluation_routes.router, prefix="/api", tags=["evaluations"])


# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Root route
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "environment": settings.APP_ENV,
    }


# Run the app
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "product_evaluator.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )