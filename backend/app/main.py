import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.readings import router as readings_router
from app.services.ai_service import AIServiceError
from app.services.reading_service import DatabaseOperationError
import app.models.reading  # noqa: F401
import app.models.user  # noqa: F401


def ensure_readings_user_column() -> None:
    inspector = inspect(engine)
    if "readings" not in inspector.get_table_names() or "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("readings")}
    with engine.begin() as conn:
        if "user_id" not in columns:
            conn.execute(text("ALTER TABLE readings ADD COLUMN user_id INTEGER NULL"))

    inspector = inspect(engine)
    indexes = {index["name"] for index in inspector.get_indexes("readings")}
    with engine.begin() as conn:
        if "ix_readings_user_id" not in indexes:
            conn.execute(text("CREATE INDEX ix_readings_user_id ON readings (user_id)"))

    inspector = inspect(engine)
    foreign_keys = inspector.get_foreign_keys("readings")
    has_user_fk = any(
        "user_id" in fk.get("constrained_columns", [])
        for fk in foreign_keys
    )
    if not has_user_fk:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE readings "
                    "ADD CONSTRAINT fk_readings_user_id_users "
                    "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"
                )
            )


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
        ensure_readings_user_column()

    app.include_router(health_router)
    app.include_router(auth_router)
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
