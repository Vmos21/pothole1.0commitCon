from datetime import datetime, timezone
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.repositories.sqlite_incidents import SQLiteIncidentRepository
from app.schemas.incident import LocationSubmission

router = APIRouter(tags=["location ingestion"])


def _single_value_form(body: bytes) -> dict[str, str]:
    return {
        key: values[-1]
        for key, values in parse_qs(body.decode("utf-8"), keep_blank_values=True).items()
        if values
    }


@router.post("/pothole_locations", status_code=201)
async def receive_android_location(request: Request) -> JSONResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip()
    if content_type == "application/json":
        try:
            payload = await request.json()
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from error
    elif content_type == "application/x-www-form-urlencoded":
        form = _single_value_form(await request.body())
        payload = {
            "latitude": form.get("pothole_location[latitude]", form.get("latitude")),
            "longitude": form.get("pothole_location[longitude]", form.get("longitude")),
        }
    else:
        raise HTTPException(
            status_code=415,
            detail="Send application/x-www-form-urlencoded or application/json",
        )

    try:
        submission = LocationSubmission.model_validate(payload)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error

    repository: SQLiteIncidentRepository = request.app.state.incident_repository
    repository.ingest_location(
        latitude=submission.latitude,
        longitude=submission.longitude,
        observed_at=submission.date_time or datetime.now(timezone.utc),
        detection_method=submission.detection_method,
        confidence=submission.confidence,
        source="android_legacy",
        source_event_id=submission.source_event_id,
        image_ref=submission.image_ref,
    )
    return JSONResponse("Location recorded", status_code=201)


@router.get("/pothole_locations.json")
def list_android_locations(request: Request) -> list[dict[str, float | str]]:
    repository: SQLiteIncidentRepository = request.app.state.incident_repository
    return repository.list_locations()
