# RoadSense

RoadSense is a prototype municipal pothole incident review tool. It builds on the location output of the upstream [pothole-detection Android app](https://github.com/ht-eml/pothole-detection) and provides a foundation for incident review, repeat-sighting grouping, road context, prioritization, and repair planning.

> **Prototype status:** The application currently uses synthetic records and illustrative repair rates. It is not connected to municipal systems, authorized camera feeds, or a production identity provider. Do not use the sample costs or incident data for operational decisions.

## Current Features

- Interactive React dashboard with an Esri street map and incident markers. Map tiles and data sources are attributed in the map.
- FastAPI service backed by a local SQLite database.
- Twelve clearly marked synthetic incidents across Bengaluru and Coimbatore, with sample repeat observations. Seed upgrades are additive and idempotent.
- Official sign-in page with an HttpOnly, signed session cookie. Incident, camera-status, and estimate routes require a session.
- Incident inspection with location, sample severity, report count, and detection metadata.
- Repeat location submissions are grouped with unresolved incidents when they are within 15 metres. An optional source event ID makes retries idempotent.
- Illustrative INR repair estimate based on area, depth, and a sample road-class allowance.
- Root-level location endpoints compatible with the upstream Android app's form-encoded coordinate submission and JSON location listing.

## Project Layout

```text
backend/
  app/
    adapters/       Integration boundaries, including the camera placeholder
    api/routes/     Authentication, incident, and location-ingest routes
    repositories/   SQLite schema, demo seeding, and incident persistence
    schemas/        API request and response validation
    services/       Repair-estimation logic
    security.py     Official session and credential handling
  data/             Runtime SQLite database (git-ignored)
  tests/            API, authentication, database, and estimation tests
frontend/
  src/              React dashboard, sign-in page, API client, and styles
  index.html        Vite entry point
  code*.html        Preserved standalone UI prototypes
```

## Run Locally

Requirements: Python 3.10+ and Node.js 20+.

### Start the API

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and replace the example password and session secret. Then run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file .env
```

The API creates `backend/data/roadsense.sqlite3` on startup and seeds the sample incidents once. Set `ROAD_SENSE_DB_PATH` to use a different SQLite file.

### Start the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` requests to FastAPI on port 8000 so the browser works with forwarded development-container URLs.

API health: [http://localhost:8000/health](http://localhost:8000/health)  
Interactive API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## Local Demo Sign-In

If no `.env` credentials are configured while running in development mode, the local demo account is:

- Email: `official@roadsense.local`
- Password: `RoadSense-Demo-2026!`

These credentials are for local demonstration only. Production mode requires explicitly configured official credentials and a strong `SESSION_SECRET`. Serve over HTTPS and set `SESSION_COOKIE_SECURE=true` in production. The current sign-in is a single-account prototype, not a municipal identity-management system.

## API Endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Public | Validate configured official credentials and issue a session cookie |
| `GET` | `/api/v1/auth/me` | Official session | Return the current official identity |
| `POST` | `/api/v1/auth/logout` | Public | Clear the session cookie |
| `GET` | `/api/v1/incidents` | Official session | List incidents with grouped observation counts |
| `GET` | `/api/v1/incidents/{id}/camera-check` | Official session | Report camera integration status; no camera is contacted |
| `POST` | `/api/v1/incidents/estimate` | Official session | Calculate an illustrative repair-cost range |
| `POST` | `/pothole_locations` | Public legacy endpoint | Accept upstream Android GPS reports |
| `GET` | `/pothole_locations.json` | Public legacy endpoint | List saved observations in the upstream app's expected shape |

The legacy Android app submits `pothole_location[latitude]` and `pothole_location[longitude]` as URL-encoded form fields and reads `latitude`, `longitude`, and `date_time` from the JSON list. Since that client sends coordinates only, detection method, confidence, and event ID remain unknown unless supplied by a newer client.

> The legacy location-ingestion routes are public for compatibility. Restrict their network exposure or add device authentication before making the API publicly accessible.

## Tests and Build

Run backend tests:

```bash
cd backend
.venv/bin/python -m pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Known Gaps

- The upstream project's Heroku service is no longer available, and its Rails server implementation was not included in the repository. This prototype accepts the same basic coordinate payload but does not connect to the old service.
- Camera feed discovery, authorization, image retrieval, and computer-vision confirmation are not implemented.
- Repeat-report matching currently uses a simple 15-metre distance rule; it does not use road segments or an adjustable time window.
- Road classes are sample/manual values. OpenStreetMap road lookup and traffic data are not connected. The map displays incident points, not verified road classifications.
- Repair estimates use replaceable demo constants, not an approved municipal rate card, measured material requirements, crew costs, or field assessment.
- Priority ranking, budget-constrained optimization, crew routing, evaluation baselines, and model training are not implemented yet.
- The synthetic locations span two cities to demonstrate map and API behavior; they are not real pothole reports.

## Suggested Next Steps

1. Confirm and document the location payload from the upstream Android app, including a stable event ID and detection metadata where possible.
2. Add authorization or device credentials to location ingestion before accepting external traffic.
3. Connect an approved OSM/traffic source and a permitted camera provider through the existing adapter boundaries.
4. Replace sample estimates with an approved rate card and capture estimate assumptions in the API response.
5. Implement explainable priority scoring and a budgeted repair planner, then evaluate against the documented baselines.
