"""
FastAPI Main Application - Modular Forex Trading Analysis Platform
Implements plugin-based architecture with extensible API endpoints
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.plugin_manager import plugin_manager
from app.core.event_system import event_manager
from app.core.config import settings
from app.api.v1 import api_router as v1_router
from app.middleware.timing import TimingMiddleware
from app.middleware.error_handling import ErrorHandlingMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - handles startup and shutdown"""
    logger.info("Starting Forex Analyzer API...")
    
    # Initialize plugin system
    try:
        await plugin_manager.load_all_plugins()
        logger.info(f"Loaded {len(plugin_manager.plugins)} plugins")
    except Exception as e:
        logger.error(f"Error loading plugins: {e}")
    
    # Emit startup event
    await event_manager.emit("app_startup", {"version": settings.VERSION})
    
    yield  # App runs here
    
    # Cleanup on shutdown
    logger.info("Shutting down Forex Analyzer API...")
    await event_manager.emit("app_shutdown")
    
    # Cleanup plugins
    for plugin_name in list(plugin_manager.plugins.keys()):
        await plugin_manager.unload_plugin(plugin_name)


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Forex Trading Analysis Platform",
    description="Modular platform for analyzing forex trading data with ML-powered insights",
    version=settings.VERSION,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TimingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Include API routers
app.include_router(v1_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    plugin_stats = plugin_manager.list_plugins()
    event_stats = event_manager.get_stats()
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "plugins": {
            "total": len(plugin_stats),
            "active": len([p for p in plugin_stats.values() if p["status"] == "active"]),
            "error": len([p for p in plugin_stats.values() if p["status"] == "error"])
        },
        "events": event_stats
    }


# Plugin management endpoints
@app.get("/api/plugins")
async def list_plugins():
    """List all available plugins and their status"""
    return plugin_manager.list_plugins()


@app.post("/api/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str):
    """Reload a specific plugin"""
    if plugin_name not in plugin_manager.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Unload and reload
    await plugin_manager.unload_plugin(plugin_name)
    success = await plugin_manager.load_plugin(plugin_name)
    
    if success:
        return {"message": f"Plugin {plugin_name} reloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to reload plugin {plugin_name}")


# Event system endpoints for debugging
@app.get("/api/events/history")
async def get_event_history(event_type: str = None, limit: int = 100):
    """Get recent event history"""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    history = event_manager.get_event_history(event_type, limit)
    return [
        {
            "type": event.type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "correlation_id": event.correlation_id,
            "metadata": event.metadata
        }
        for event in history
    ]


@app.get("/api/events/stats")
async def get_event_stats():
    """Get event system statistics"""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    return event_manager.get_stats()


# Serve static files in production
if settings.ENVIRONMENT == "production":
    # Mount static files for production deployment
    static_path = Path("static")
    if static_path.exists():
        app.mount("/", StaticFiles(directory="static", html=True), name="static")


# Custom exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}")
    
    if settings.ENVIRONMENT == "development":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )