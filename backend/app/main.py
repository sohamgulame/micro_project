import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.routes.health import router as health_router
from app.routes.readings import router as readings_router
from app.services.ai_service import AIServiceError
from app.services.reading_service import DatabaseOperationError
import app.models.reading  # noqa: F401


def create_application() -> FastAPI:
    app = FastAPI(
        title="IoT Health Monitoring System",
        version="0.1.0",
        description="Backend API for monitoring IoT health data.",
    )

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(readings_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "message": "Invalid reading payload.",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(DatabaseOperationError)
    async def database_exception_handler(
        request: Request, exc: DatabaseOperationError
    ) -> JSONResponse:
        return JSONResponse(status_code=500, content={"message": str(exc)})

    @app.exception_handler(AIServiceError)
    async def ai_exception_handler(
        request: Request, exc: AIServiceError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"message": str(exc)})

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred."},
        )

    return app


app = create_application()
