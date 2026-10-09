# CommitCon (Second Year, Non-Circuit): Plans for Both Shortlisted Ideas

Shortlist:
- **Option A:** #5 Smart Road Pothole Prioritization System
- **Option B:** #2 Smart Classroom Allocation System

**Rule of thumb for both:** every bullet in the PS ends in "measurable, compared to a baseline, explainable". Build a small core well, then spend real time on the evaluation layer. That is what gets scored.

---

## Quick Comparison

| | A: Pothole Prioritization | B: Classroom Allocation |
|---|---|---|
| Core technique | YOLO detection + weighted scoring + budgeted planning (knapsack / clustering) | Constraint optimization (OR-Tools CP-SAT) |
| Difficulty | Medium-High (more moving parts) | Medium (one strong solver) |
| Demo appeal | High (map, images, live ranking) | Medium (needs a strong live-disruption demo) |
| Main risk | Scope creep on the detector; no ground truth for "correct" priority | Looks dry; many teams choose it |
| Baseline to beat | FCFS and severity-only | Greedy first-fit |
| Data | Public pothole dataset + synthetic reports | Fully synthetic (or anonymized real) |

**Pick A** if you want the more memorable demo and someone on the team is comfortable with a bit of computer vision.
**Pick B** if you want a reliable finish with a clean evaluation story.

---

# Option A: Smart Road Pothole Prioritization System

## 1. Goal
Detect road damage from available data, then tell authorities **which potholes to fix first** given a limited maintenance budget, with a clear explanation for every ranking.

## 2. PS Requirement Mapping

| PS requirement | How we cover it |
|---|---|
| Identify and represent road damage | YOLOv8 detector on images; each detection becomes a structured pothole record |
| Consider multiple factors | Weighted score: severity, traffic, road importance, report count/age |
| Account for limited resources | Budgeted planner (crew-hours / cost cap) |
| Understandable basis | Per-pothole factor breakdown ("ranked #2 because...") |
| Support maintenance planning | Cluster nearby potholes into crew trips; route order |
| Evaluate effectiveness | Simulation vs baselines on risk removed and travel distance |

## 3. System Architecture

```
Images / reports  ->  Detector (YOLOv8n)  ->  Pothole records (DB)
                                                   |
OSM road data (class, importance) ----------------+
Traffic estimate (by road class / synthetic) -----+
                                                   v
                                       Priority scorer (explainable)
                                                   v
                                    Budgeted planner + clustering
                                                   v
                         Map dashboard + evaluation report
```

## 4. Components

### 4.1 Detection
- Fine-tune **YOLOv8n** on a public pothole dataset (Kaggle / Roboflow Universe).
- Output: bounding box, confidence.
- **Severity estimate:** relative box area (box area / image or lane area) mapped to Small / Medium / Large, or a normalized 0-1 value.
- Keep this module time-boxed. A decent mAP is enough; the product is the prioritization.

### 4.2 Data Model
Each pothole record:
- `id`, `lat`, `lon`, `image_path`
- `severity` (0-1), `confidence`
- `road_class` (highway / arterial / local), from OpenStreetMap
- `traffic_score` (0-1), estimated from road class or synthetic
- `report_count`, `first_reported_at`
- `status` (open / scheduled / fixed)

### 4.3 Priority Score
```
score = w1*severity + w2*traffic + w3*road_importance + w4*age_or_reports
```
- Normalize each factor to 0-1.
- Store the per-factor contributions and show them in the UI (explainability).
- Expose weights as sliders so judges can see the ranking change live.

### 4.4 Planner (Limited Resources + Nearby Clustering)
- Each repair has a cost (crew-hours or rupees, scaled by severity).
- Given budget B, select the set of potholes maximizing total **risk removed** (`severity * traffic`). This is a 0/1 knapsack.
- **Clustering:** group nearby potholes (DBSCAN on coordinates or road-segment grouping) so one crew trip fixes several; add a travel-cost term using a nearest-neighbour route.
- Output: ordered repair plan with trips and estimated distance.

### 4.5 Dashboard
- Leaflet map with markers colored by priority.
- Click a marker to see image, score breakdown, and why it was ranked there.
- Controls: budget input, weight sliders, "run planner" button.
- Evaluation tab with baseline comparison charts.

## 5. Evaluation Plan

Define metrics up front:
- **Risk removed:** sum of `severity * traffic` of repaired potholes within the budget.
- **Total travel distance** for the repair plan.
- **High-severity coverage:** fraction of Large potholes repaired.

Baselines:
1. First-come-first-served
2. Severity-only
3. Random

Method: simulate 100+ random scenarios (random pothole sets and budgets), report mean and spread per strategy in a table and a chart. Also show a **sensitivity analysis** (how rankings change as weights vary).

## 6. Data Strategy
- Real geotagged pothole reports are scarce, so **generate synthetic reports** along real Coimbatore roads from OSM and clearly label them as synthetic.
- Use a handful of real detected images to show the full pipeline works end to end.
- State assumptions (traffic proxy, cost model) explicitly in the README.

## 7. Suggested Tech Stack
- **Detection and backend:** Python, Ultralytics YOLOv8, FastAPI
- **Planner:** NumPy / SciPy, scikit-learn (DBSCAN)
- **Geo data:** OSMnx / Overpass API
- **Frontend:** React + Leaflet
- **Storage:** SQLite or PostgreSQL

## 8. Build Phases
1. **Setup:** dataset, environment, project skeleton, synthetic data generator
2. **Detector:** train and run inference, save structured records
3. **Scoring:** priority function with breakdown output
4. **Planner:** knapsack + clustering + route
5. **Dashboard:** map, explanation panel, controls
6. **Evaluation:** simulation harness, baseline comparison, charts
7. **Polish:** README, demo script, slides, rehearsal

## 9. Demo Script
1. Upload a road image and show the detection with severity.
2. Show the map with ranked potholes; click one to show its explanation.
3. Set a budget and run the planner; show trips grouped by area.
4. Drag a weight slider and show the ranking change.
5. Show the evaluation table where our strategy beats FCFS and severity-only.

## 10. Risks and Mitigations
- **Detector time sink:** time-box it; use a pretrained checkpoint and fine-tune briefly.
- **No ground truth for "correct" priority:** evaluate on *risk removed under budget*, a clearly defined metric.
- **Weak map data:** fall back to a synthetic road graph if OSM extraction is slow.

