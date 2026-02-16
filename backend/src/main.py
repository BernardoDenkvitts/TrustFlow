"""TrustFlow Backend"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.modules.agreements.http.exceptions_handler import (
    register_agreements_exception_handlers,
)
from src.modules.agreements.http.router import router as agreements_router
from src.modules.auth.http.router import router as auth_router
from src.modules.auth.worker import SessionCleanupWorker
from src.modules.disputes.http.exceptions_handler import (
    register_disputes_exception_handlers,
)
from src.modules.disputes.http.router import router as disputes_router
from src.modules.users.http.exceptions_handler import register_users_exception_handlers
from src.modules.users.http.router import router as users_router
from src.modules.auth.http.exceptions_handler import (
    register_auth_exception_handlers
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan."""
    # Startup
    session_cleanup_worker = SessionCleanupWorker()
    await session_cleanup_worker.start()
    
    yield
    
    # Shutdown
    await session_cleanup_worker.stop()


app = FastAPI(
    title=settings.app_name,
    description="Escrow payment platform with ETH guarantee",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api/v1")
app.include_router(agreements_router, prefix="/api/v1")
app.include_router(disputes_router, prefix="/api/v1")

# Register exception handlers
register_users_exception_handlers(app)
register_agreements_exception_handlers(app)
register_disputes_exception_handlers(app)
register_auth_exception_handlers(app)

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

