from fastapi import FastAPI
from routers import router
from dependencies import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()

    # Initialize database
    init_db()

    # Include routers (each route handler declares its own get_db dependency)
    app.include_router(router, prefix="/api")

    return app


app = create_app()
