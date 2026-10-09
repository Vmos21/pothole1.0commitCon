# Project Specification: Smart Road Pothole Prioritization System

## 1. Project Goal
The primary objective is to detect road damage from available data[cite: 1]. Following detection, the system must tell authorities which potholes to fix first given a limited maintenance budget[cite: 1]. Crucially, it must provide a clear explanation for every ranking[cite: 1]. 

## 2. System Architecture & Tech Stack
*   **Detection and backend:** Python, Ultralytics YOLOv8, and FastAPI[cite: 1].
*   **Planner:** NumPy and SciPy, alongside scikit-learn for DBSCAN[cite: 1].
*   **Geo data:** OSMnx and Overpass API[cite: 1].
*   **Frontend:** React combined with Leaflet[cite: 1].
*   **Storage:** SQLite or PostgreSQL[cite: 1].

## 3. Core Components

### 3.1 Detection Pipeline
*   The system will fine-tune YOLOv8n on a public pothole dataset sourced from Kaggle or Roboflow Universe[cite: 1].
*   The detector's output must include a bounding box and a confidence metric[cite: 1].
*   Severity is estimated using the relative box area, which is then mapped to Small, Medium, or Large, or converted to a normalized 0-1 value[cite: 1].

### 3.2 Data Model
Each pothole record must contain the following fields:
*   `id`, `lat`, `lon`, and `image_path`[cite: 1].
*   `severity` (0-1) and `confidence`[cite: 1].
*   `road_class` (such as highway, arterial, or local), derived from OpenStreetMap[cite: 1].
*   `traffic_score` (0-1), which is estimated from the road class or synthetic data[cite: 1].
*   `report_count` and `first_reported_at`[cite: 1].
*   `status`, tracked as open, scheduled, or fixed[cite: 1].

### 3.3 Priority Scoring
*   The priority score is calculated as: `score = w1*severity + w2*traffic + w3*road_importance + w4*age_or_reports`[cite: 1].
*   Each of these factors must be normalized to a 0-1 scale[cite: 1].
*   The system needs to store the per-factor contributions and display them in the UI to ensure explainability[cite: 1].
*   Weights should be exposed as sliders so judges can observe live ranking changes[cite: 1].

### 3.4 Budgeted Planner
*   The planner assumes each repair has a cost, measured in crew-hours or rupees, scaled by severity[cite: 1].
*   Given a budget B, the system uses a 0/1 knapsack approach to select the set of potholes maximizing total risk removed, defined as `severity * traffic`[cite: 1].
*   To optimize logistics, nearby potholes are clustered using DBSCAN on coordinates or road-segment grouping so a single crew trip can fix several[cite: 1].
*   A travel-cost term is added using a nearest-neighbour route[cite: 1].
*   The final output is an ordered repair plan detailing trips and estimated distance[cite: 1].

## 4. UI Dashboard & Evaluation Strategy
*   The dashboard features a Leaflet map populated with markers colored according to their priority[cite: 1].
*   Clicking a marker reveals the image, the score breakdown, and an explanation of why it was ranked there[cite: 1].
*   The interface must include budget input controls, weight sliders, and a "run planner" button[cite: 1].
*   An evaluation tab is required to display baseline comparison charts[cite: 1].
*   The evaluation metrics defined up front are risk removed, total travel distance, and high-severity coverage[cite: 1].
*   The system's performance will be simulated across 100+ random scenarios and compared against First-come-first-served, Severity-only, and Random baselines[cite: 1].