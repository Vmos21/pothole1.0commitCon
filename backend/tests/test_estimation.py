from app.schemas.incident import EstimateRequest
from app.services.estimation import estimate_repair


def test_estimate_increases_for_highway_access_allowance() -> None:
    arterial = estimate_repair(
        EstimateRequest(area_m2=1.8, depth_cm=9.4, road_class="arterial")
    )
    highway = estimate_repair(
        EstimateRequest(area_m2=1.8, depth_cm=9.4, road_class="highway")
    )

    assert highway.midpoint_inr > arterial.midpoint_inr
    assert arterial.low_inr < arterial.midpoint_inr < arterial.high_inr


def test_depth_does_not_add_adjustment_below_three_cm() -> None:
    shallow = estimate_repair(
        EstimateRequest(area_m2=1, depth_cm=2, road_class="local")
    )
    at_threshold = estimate_repair(
        EstimateRequest(area_m2=1, depth_cm=3, road_class="local")
    )

    assert shallow.midpoint_inr == at_threshold.midpoint_inr
