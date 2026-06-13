from fastapi import FastAPI
from routers import router
from dependencies import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()

    # Initialize database
    init_db()

    # Include routers (DB session dependency is declared per-handler in routers.py)
    app.include_router(router, prefix="/api")

    return app


app = create_app()
