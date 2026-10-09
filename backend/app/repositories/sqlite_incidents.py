import math
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from app.schemas.incident import Incident


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    road_name TEXT NOT NULL,
    severity REAL NOT NULL CHECK (severity BETWEEN 0 AND 1),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    depth_cm REAL NOT NULL CHECK (depth_cm >= 0),
    area_m2 REAL NOT NULL CHECK (area_m2 > 0),
    road_class TEXT NOT NULL CHECK (road_class IN ('local', 'collector', 'arterial', 'highway')),
    status TEXT NOT NULL CHECK (status IN ('open', 'scheduled', 'fixed')),
    detected_by TEXT NOT NULL CHECK (detected_by IN ('vision', 'sensor', 'unknown')),
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    observed_at TEXT NOT NULL,
    detection_method TEXT NOT NULL CHECK (detection_method IN ('vision', 'sensor', 'unknown')),
    confidence REAL CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    source TEXT NOT NULL,
    source_event_id TEXT,
    image_ref TEXT,
    UNIQUE (source, source_event_id)
);

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_observations_incident_time ON observations(incident_id, observed_at);
"""


_SAMPLE_INCIDENTS = [
    {
        "id": "RW-2026-00412",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "road_name": "Outer Ring Road · Junction 4B",
        "severity": 0.94,
        "confidence": 0.91,
        "depth_cm": 9.4,
        "area_m2": 1.8,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "vision",
        "observations": 3,
    },
    {
        "id": "RW-2026-00398",
        "latitude": 12.9716,
        "longitude": 77.6412,
        "road_name": "Indiranagar 100ft Road",
        "severity": 0.82,
        "confidence": 0.88,
        "depth_cm": 8.7,
        "area_m2": 1.2,
        "road_class": "collector",
        "status": "open",
        "detected_by": "sensor",
        "observations": 2,
    },
]

_ADDITIONAL_SAMPLE_INCIDENTS = [
    {
        "id": "RW-2026-00501",
        "latitude": 11.0192,
        "longitude": 76.9966,
        "road_name": "Coimbatore · Avinashi Road, Peelamedu",
        "severity": 0.89,
        "confidence": 0.93,
        "depth_cm": 7.8,
        "area_m2": 1.4,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "vision",
        "observations": 4,
    },
    {
        "id": "RW-2026-00502",
        "latitude": 10.9978,
        "longitude": 76.9828,
        "road_name": "Coimbatore · Trichy Road, Ramanathapuram",
        "severity": 0.72,
        "confidence": 0.86,
        "depth_cm": 5.3,
        "area_m2": 0.9,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "sensor",
        "observations": 2,
    },
    {
        "id": "RW-2026-00503",
        "latitude": 11.0260,
        "longitude": 76.9555,
        "road_name": "Coimbatore · Mettupalayam Road, Saibaba Colony",
        "severity": 0.58,
        "confidence": 0.81,
        "depth_cm": 3.8,
        "area_m2": 0.7,
        "road_class": "collector",
        "status": "open",
        "detected_by": "vision",
        "observations": 1,
    },
    {
        "id": "RW-2026-00504",
        "latitude": 11.0401,
        "longitude": 76.9970,
        "road_name": "Coimbatore · Sathy Road, Ganapathy",
        "severity": 0.84,
        "confidence": 0.9,
        "depth_cm": 6.7,
        "area_m2": 1.1,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "sensor",
        "observations": 3,
    },
    {
        "id": "RW-2026-00505",
        "latitude": 10.9920,
        "longitude": 76.9610,
        "road_name": "Coimbatore · Ukkadam bus stand",
        "severity": 0.96,
        "confidence": 0.95,
        "depth_cm": 10.2,
        "area_m2": 2.1,
        "road_class": "arterial",
        "status": "scheduled",
        "detected_by": "vision",
        "observations": 5,
    },
    {
        "id": "RW-2026-00506",
        "latitude": 12.9279,
        "longitude": 77.6763,
        "road_name": "Bengaluru · Outer Ring Road, Bellandur",
        "severity": 0.88,
        "confidence": 0.92,
        "depth_cm": 8.1,
        "area_m2": 1.5,
        "road_class": "highway",
        "status": "open",
        "detected_by": "vision",
        "observations": 3,
    },
    {
        "id": "RW-2026-00507",
        "latitude": 12.9090,
        "longitude": 77.6770,
        "road_name": "Bengaluru · Sarjapur Main Road, Kaikondrahalli",
        "severity": 0.77,
        "confidence": 0.89,
        "depth_cm": 6.1,
        "area_m2": 1.0,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "sensor",
        "observations": 2,
    },
    {
        "id": "RW-2026-00508",
        "latitude": 12.9738,
        "longitude": 77.6165,
        "road_name": "Bengaluru · MG Road, Trinity Circle",
        "severity": 0.63,
        "confidence": 0.84,
        "depth_cm": 4.2,
        "area_m2": 0.8,
        "road_class": "collector",
        "status": "open",
        "detected_by": "vision",
        "observations": 1,
    },
    {
        "id": "RW-2026-00509",
        "latitude": 12.9595,
        "longitude": 77.6592,
        "road_name": "Bengaluru · Old Airport Road, HAL",
        "severity": 0.74,
        "confidence": 0.87,
        "depth_cm": 5.9,
        "area_m2": 1.2,
        "road_class": "arterial",
        "status": "open",
        "detected_by": "sensor",
        "observations": 2,
    },
    {
        "id": "RW-2026-00510",
        "latitude": 12.9452,
        "longitude": 77.5256,
        "road_name": "Bengaluru · Mysore Road, Nayandahalli",
        "severity": 0.81,
        "confidence": 0.9,
        "depth_cm": 6.8,
        "area_m2": 1.3,
        "road_class": "highway",
        "status": "open",
        "detected_by": "vision",
        "observations": 3,
    },
]


class SQLiteIncidentRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(_SCHEMA)
            seeded = connection.execute(
                "INSERT OR IGNORE INTO app_metadata (key, value) VALUES (?, ?)",
                ("demo_seed_v1", "complete"),
            ).rowcount
            if seeded:
                self._seed_demo_data(connection)
            added_v2 = connection.execute(
                "INSERT OR IGNORE INTO app_metadata (key, value) VALUES (?, ?)",
                ("demo_seed_v2", "complete"),
            ).rowcount
            if added_v2:
                self._seed_demo_data(connection, _ADDITIONAL_SAMPLE_INCIDENTS)

    def _seed_demo_data(
        self,
        connection: sqlite3.Connection,
        samples: list[dict[str, str | float | int]] = _SAMPLE_INCIDENTS,
    ) -> None:
        now = datetime.now(timezone.utc)
        for sample in samples:
            incident = {key: value for key, value in sample.items() if key != "observations"}
            connection.execute(
                """INSERT INTO incidents (
                    id, latitude, longitude, road_name, severity, confidence,
                    depth_cm, area_m2, road_class, status, detected_by, is_demo, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    incident["id"], incident["latitude"], incident["longitude"],
                    incident["road_name"], incident["severity"], incident["confidence"],
                    incident["depth_cm"], incident["area_m2"], incident["road_class"],
                    incident["status"], incident["detected_by"],
                    (now - timedelta(days=2)).isoformat(),
                ),
            )
            for index in range(sample["observations"]):
                connection.execute(
                    """INSERT INTO observations (
                        id, incident_id, latitude, longitude, observed_at,
                        detection_method, confidence, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()), incident["id"], incident["latitude"],
                        incident["longitude"],
                        (now - timedelta(hours=(sample["observations"] - index) * 5)).isoformat(),
                        incident["detected_by"], incident["confidence"], "demo_seed",
                    ),
                )

    def list_incidents(self) -> list[Incident]:
        with self._connection() as connection:
            rows = connection.execute(
                self._incident_query() + " ORDER BY incidents.created_at DESC"
            ).fetchall()
        return [self._to_incident(row) for row in rows]

    def get_incident(self, incident_id: str) -> Incident | None:
        with self._connection() as connection:
            row = connection.execute(
                self._incident_query("WHERE incidents.id = ?"), (incident_id,)
            ).fetchone()
        return self._to_incident(row) if row else None

    def list_locations(self) -> list[dict[str, float | str]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT latitude, longitude, observed_at AS date_time
                   FROM observations ORDER BY observed_at DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def ingest_location(
        self,
        latitude: float,
        longitude: float,
        observed_at: datetime,
        detection_method: str = "unknown",
        confidence: float | None = None,
        source: str = "android_legacy",
        source_event_id: str | None = None,
        image_ref: str | None = None,
        match_distance_m: float = 15,
    ) -> tuple[Incident, bool]:
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        observed_at_text = observed_at.astimezone(timezone.utc).isoformat()

        with self._connection() as connection:
            incident_id = None
            if source_event_id:
                existing = connection.execute(
                    "SELECT incident_id FROM observations WHERE source = ? AND source_event_id = ?",
                    (source, source_event_id),
                ).fetchone()
                if existing:
                    incident_id = existing["incident_id"]
                    return self._get_incident(connection, incident_id), False

            candidates = connection.execute(
                """SELECT id, latitude, longitude FROM incidents
                   WHERE status IN ('open', 'scheduled') AND is_demo = 0"""
            ).fetchall()
            nearest = min(
                (
                    (self._distance_m(latitude, longitude, row["latitude"], row["longitude"]), row["id"])
                    for row in candidates
                ),
                default=(float("inf"), None),
            )
            is_new_incident = nearest[0] > match_distance_m
            incident_id = nearest[1] if not is_new_incident else self._new_incident_id(observed_at)

            if is_new_incident:
                connection.execute(
                    """INSERT INTO incidents (
                        id, latitude, longitude, road_name, severity, confidence,
                        depth_cm, area_m2, road_class, status, detected_by, is_demo, created_at
                    ) VALUES (?, ?, ?, ?, 0, 0, 0, 0.1, 'local', 'open', ?, 0, ?)""",
                    (
                        incident_id, latitude, longitude, "Road segment · geocoding pending",
                        detection_method, observed_at_text,
                    ),
                )

            connection.execute(
                """INSERT INTO observations (
                    id, incident_id, latitude, longitude, observed_at,
                    detection_method, confidence, source, source_event_id, image_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), incident_id, latitude, longitude, observed_at_text,
                    detection_method, confidence, source, source_event_id, image_ref,
                ),
            )
            return self._get_incident(connection, incident_id), is_new_incident

    @staticmethod
    def _incident_query(where_clause: str = "") -> str:
        return """SELECT incidents.*, COUNT(observations.id) AS report_count
                  FROM incidents LEFT JOIN observations ON observations.incident_id = incidents.id
                  """ + where_clause + " GROUP BY incidents.id"

    def _get_incident(self, connection: sqlite3.Connection, incident_id: str) -> Incident:
        row = connection.execute(
            self._incident_query("WHERE incidents.id = ?"), (incident_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"Incident {incident_id} not found")
        return self._to_incident(row)

    @staticmethod
    def _to_incident(row: sqlite3.Row) -> Incident:
        return Incident(
            id=row["id"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            road_name=row["road_name"],
            severity=row["severity"],
            confidence=row["confidence"],
            depth_cm=row["depth_cm"],
            area_m2=row["area_m2"],
            road_class=row["road_class"],
            report_count=row["report_count"],
            status=row["status"],
            detected_by=row["detected_by"],
            is_demo=bool(row["is_demo"]),
        )

    @staticmethod
    def _new_incident_id(observed_at: datetime) -> str:
        return f"RW-{observed_at.year}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_m = 6_371_000
        lat_delta = math.radians(lat2 - lat1)
        lon_delta = math.radians(lon2 - lon1)
        haversine = (
            math.sin(lat_delta / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(lon_delta / 2) ** 2
        )
        return 2 * radius_m * math.asin(math.sqrt(haversine))
