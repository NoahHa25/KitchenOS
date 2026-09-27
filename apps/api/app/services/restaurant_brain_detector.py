from dataclasses import dataclass


@dataclass(frozen=True)
class RepeatedProblemDetection:
    detected: bool
    title: str | None = None
    description: str | None = None
    severity: str = "medium"
    confidence: str = "medium"
    evidence: str | None = None


def detect_repeated_problem(
    problem_name: str,
    occurrence_count: int,
    time_window_days: int = 30,
    threshold: int = 3,
) -> RepeatedProblemDetection:
    """
    Detect whether a problem has occurred frequently enough
    to be considered a recurring operational problem.

    The detector is intentionally deterministic for Brain V1.
    """

    if occurrence_count < threshold:
        return RepeatedProblemDetection(
            detected=False,
        )

    if occurrence_count >= 5:
        severity = "high"
        confidence = "high"
    elif occurrence_count >= 4:
        severity = "high"
        confidence = "medium"
    else:
        severity = "medium"
        confidence = "medium"

    plural = "occurrence" if occurrence_count == 1 else "occurrences"

    return RepeatedProblemDetection(
        detected=True,
        title=f"{problem_name} is recurring",
        description=(
            f"{problem_name} occurred {occurrence_count} times "
            f"during the last {time_window_days} days."
        ),
        severity=severity,
        confidence=confidence,
        evidence=(
            f"{occurrence_count} {plural} during "
            f"the last {time_window_days} days."
        ),
    )