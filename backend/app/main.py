import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.routes.location_ingest import router as location_ingest_router
from app.repositories.sqlite_incidents import SQLiteIncidentRepository


def create_app(database_path: str | Path | None = None) -> FastAPI:
    default_path = Path(__file__).resolve().parents[1] / "data" / "roadsense.sqlite3"
    repository = SQLiteIncidentRepository(
        database_path or os.environ.get("ROAD_SENSE_DB_PATH", default_path)
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        repository.initialize()
        yield

    application = FastAPI(
        title="RoadSense API",
        description="Incident review API backed by a local SQLite sample database.",
        version="0.2.0",
        lifespan=lifespan,
    )
    application.state.incident_repository = repository
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    application.include_router(router, prefix="/api/v1")
    application.include_router(location_ingest_router)

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "mode": "sqlite-sample"}

    return application


app = create_app()
