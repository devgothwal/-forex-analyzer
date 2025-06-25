"""
API v1 Router - Main API endpoints with plugin support
"""

from fastapi import APIRouter
from .endpoints import (
    analysis,
    data_upload,
    insights,
    plugins,
    visualizations
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    data_upload.router,
    prefix="/data",
    tags=["data"]
)

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["analysis"]
)

api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
)

api_router.include_router(
    visualizations.router,
    prefix="/visualizations",
    tags=["visualizations"]
)

api_router.include_router(
    plugins.router,
    prefix="/plugins",
    tags=["plugins"]
)