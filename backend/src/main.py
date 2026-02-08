"""TrustFlow Backend"""

from fastapi import FastAPI

from src.config import settings
from src.modules.agreements.http.exceptions_handler import (
    register_agreements_exception_handlers,
)
from src.modules.agreements.http.router import router as agreements_router
from src.modules.disputes.http.exceptions_handler import (
    register_disputes_exception_handlers,
)
from src.modules.disputes.http.router import router as disputes_router
from src.modules.users.http.exceptions_handler import register_users_exception_handlers
from src.modules.users.http.router import router as users_router


app = FastAPI(
    title=settings.app_name,
    description="Escrow payment platform with ETH guarantee",
    version="0.1.0",
    debug=settings.debug,
)

# Register routers
app.include_router(users_router, prefix="/api/v1")
app.include_router(agreements_router, prefix="/api/v1")
app.include_router(disputes_router, prefix="/api/v1")

# Register exception handlers
register_users_exception_handlers(app)
register_agreements_exception_handlers(app)
register_disputes_exception_handlers(app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

