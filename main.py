from fastapi import FastAPI
from routers import router
from dependencies import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()

    # Initialize database
    init_db()

    # Include routers (get_db is injected per-endpoint via Depends in each route handler)
    app.include_router(router, prefix="/api")

    return app


app = create_app()
