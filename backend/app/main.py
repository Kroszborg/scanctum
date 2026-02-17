from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.middleware import RequestIDMiddleware, TimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    from app.db.engine import async_engine
    await async_engine.dispose()


app = FastAPI(
    title="Scanctum",
    description="Modular Web Application Security Scanner",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware - CORS must be added LAST (first in execution order)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handler to ensure CORS headers on all responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return with CORS headers."""
    import traceback
    
    # Log the full traceback
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    
    # Get the origin from the request
    origin = request.headers.get("origin", "*")
    
    # Create response with explicit CORS headers
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
    
    # Manually add CORS headers
    response.headers["Access-Control-Allow-Origin"] = origin if origin in settings.BACKEND_CORS_ORIGINS else settings.BACKEND_CORS_ORIGINS[0]
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
