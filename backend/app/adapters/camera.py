from typing import Protocol

from app.schemas.incident import CameraCheckResponse, Incident


class CameraEvidenceAdapter(Protocol):
    async def check(self, incident: Incident) -> CameraCheckResponse: ...


class UnavailableCameraAdapter:
    async def check(self, incident: Incident) -> CameraCheckResponse:
        return CameraCheckResponse(
            detail=(
                "Camera integration is not configured. No camera feed was queried "
                f"for incident {incident.id}."
            )
        )


unavailable_camera_adapter: CameraEvidenceAdapter = UnavailableCameraAdapter()
