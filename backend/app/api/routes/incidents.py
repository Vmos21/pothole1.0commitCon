from fastapi import APIRouter, Depends, HTTPException, Request

from app.adapters.camera import unavailable_camera_adapter
from app.repositories.sqlite_incidents import SQLiteIncidentRepository
from app.schemas.incident import (
    CameraCheckResponse,
    EstimateRequest,
    EstimateResponse,
    Incident,
)
from app.security import require_official
from app.services.estimation import estimate_repair

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    dependencies=[Depends(require_official)],
)


@router.get("", response_model=list[Incident])
def list_incidents(request: Request) -> list[Incident]:
    repository: SQLiteIncidentRepository = request.app.state.incident_repository
    return repository.list_incidents()


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, request: Request) -> Incident:
    repository: SQLiteIncidentRepository = request.app.state.incident_repository
    incident = repository.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/camera-check", response_model=CameraCheckResponse)
async def check_camera_evidence(incident_id: str, request: Request) -> CameraCheckResponse:
    repository: SQLiteIncidentRepository = request.app.state.incident_repository
    incident = repository.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await unavailable_camera_adapter.check(incident)


@router.post("/estimate", response_model=EstimateResponse)
def create_estimate(request: EstimateRequest) -> EstimateResponse:
    return estimate_repair(request)
