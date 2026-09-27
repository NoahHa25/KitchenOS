from app.services.restaurant_brain_detector import (
    detect_repeated_problem,
)


def test_repeated_problem_is_not_detected_below_threshold():
    result = detect_repeated_problem(
        problem_name="Tomato shortage",
        occurrence_count=2,
        time_window_days=30,
        threshold=3,
    )

    assert result.detected is False
    assert result.title is None
    assert result.description is None


def test_repeated_problem_is_detected_at_threshold():
    result = detect_repeated_problem(
        problem_name="Tomato shortage",
        occurrence_count=3,
        time_window_days=30,
        threshold=3,
    )

    assert result.detected is True
    assert result.title == "Tomato shortage is recurring"
    assert (
        result.description
        == "Tomato shortage occurred 3 times during the last 30 days."
    )
    assert result.severity == "medium"
    assert result.confidence == "medium"


def test_four_occurrences_have_high_severity():
    result = detect_repeated_problem(
        problem_name="Supplier delay",
        occurrence_count=4,
        time_window_days=30,
        threshold=3,
    )

    assert result.detected is True
    assert result.severity == "high"
    assert result.confidence == "medium"


def test_five_or_more_occurrences_have_high_confidence():
    result = detect_repeated_problem(
        problem_name="Equipment failure",
        occurrence_count=5,
        time_window_days=30,
        threshold=3,
    )

    assert result.detected is True
    assert result.severity == "high"
    assert result.confidence == "high"


def test_custom_threshold_is_respected():
    result = detect_repeated_problem(
        problem_name="Waste spike",
        occurrence_count=4,
        time_window_days=14,
        threshold=5,
    )

    assert result.detected is False


def test_evidence_contains_occurrence_count_and_time_window():
    result = detect_repeated_problem(
        problem_name="Tomato shortage",
        occurrence_count=6,
        time_window_days=30,
        threshold=3,
    )

    assert result.detected is True
    assert result.evidence == (
        "6 occurrences during the last 30 days."
    )