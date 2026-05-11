from fastapi import FastAPI
from routers import router
from dependencies import init_db


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(docs_url=None, redoc_url=None)

    # Initialize database
    init_db()

    # Include routers
    app.include_router(router, prefix="/api")

    return app


app = create_app()
