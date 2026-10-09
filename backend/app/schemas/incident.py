from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RoadClass = Literal["local", "collector", "arterial", "highway"]


class Incident(BaseModel):
    id: str
    latitude: float
    longitude: float
    road_name: str
    severity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    depth_cm: float = Field(ge=0)
    area_m2: float = Field(gt=0)
    road_class: RoadClass
    report_count: int = Field(ge=1)
    status: Literal["open", "scheduled", "fixed"]
    detected_by: Literal["vision", "sensor", "unknown"]
    is_demo: bool = True


class EstimateRequest(BaseModel):
    area_m2: float = Field(gt=0, le=10000)
    depth_cm: float = Field(ge=0, le=200)
    road_class: RoadClass


class EstimateResponse(BaseModel):
    low_inr: int
    midpoint_inr: int
    high_inr: int
    area_m2: float
    depth_cm: float
    road_class: RoadClass
    assumptions: list[str]
    is_demo: bool = True


class CameraCheckResponse(BaseModel):
    status: Literal["not_configured"] = "not_configured"
    provider: str = "unconfigured"
    detail: str


class LocationSubmission(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    date_time: datetime | None = None
    detection_method: Literal["vision", "sensor", "unknown"] = "unknown"
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_event_id: str | None = None
    image_ref: str | None = None
