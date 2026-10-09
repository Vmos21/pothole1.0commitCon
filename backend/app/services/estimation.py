from app.schemas.incident import EstimateRequest, EstimateResponse

BASE_RATE_INR_PER_M2 = 4800
ROAD_ACCESS_ALLOWANCE_INR = {
    "local": 1200,
    "collector": 2500,
    "arterial": 5000,
    "highway": 9000,
}


def estimate_repair(request: EstimateRequest) -> EstimateResponse:
    depth_factor = 1 + max(0, request.depth_cm - 3) * 0.035
    access_allowance = ROAD_ACCESS_ALLOWANCE_INR[request.road_class]
    midpoint = round(
        request.area_m2 * BASE_RATE_INR_PER_M2 * depth_factor + access_allowance
    )

    return EstimateResponse(
        low_inr=round(midpoint * 0.8),
        midpoint_inr=midpoint,
        high_inr=round(midpoint * 1.2),
        area_m2=request.area_m2,
        depth_cm=request.depth_cm,
        road_class=request.road_class,
        assumptions=[
            f"Illustrative base rate: INR {BASE_RATE_INR_PER_M2} per square metre",
            f"Road access allowance: INR {access_allowance}",
            "Depth adjustment applies above 3 cm",
            "Range is midpoint +/- 20%; replace with an approved municipal rate card",
        ],
    )
