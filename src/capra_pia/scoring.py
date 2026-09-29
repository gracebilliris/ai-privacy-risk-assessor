from __future__ import annotations

import math
from collections import defaultdict

from capra_pia.models import (
    AssessmentRequest,
    AssessmentResult,
    CategoryScore,
    CrossReference,
    FlaggedRisk,
    Risk,
    RiskRating,
)


def _round_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _top_tertile_thresholds(risks: list[Risk]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for risk in risks:
        grouped[risk.source_paper].append(risk.frequency_pct)

    thresholds: dict[str, float] = {}
    for source_paper, values in grouped.items():
        ordered = sorted(values, reverse=True)
        top_count = max(1, math.ceil(len(ordered) / 3))
        thresholds[source_paper] = ordered[top_count - 1]
    return thresholds


def _build_recommendation(risk: Risk) -> str:
    definition = " ".join(risk.definition.split())
    return f"Prioritise controls for {risk.id} ({risk.name}): {definition}"


def assess(
    request: AssessmentRequest, risks: list[Risk], cross_refs: list[CrossReference]
) -> AssessmentResult:
    """
    Score an assessment:
    - present risks count against their category's applicable total
    - overall_score_pct = present / applicable across all rated risks
    - flag PRESENT risks whose frequency_pct is in the top tertile of their
      source paper's risks as "flagged_high_risk"
    - any risk id in `risks` not present in request.ratings goes into
      unrated_risks
    - generate short textual recommendations per flagged risk using its
      definition (no fabricated claims — reference risk.definition text)
    """

    risk_by_id = {risk.id: risk for risk in risks}
    seen_ids: set[str] = set()
    ratings_by_id: dict[str, RiskRating] = {}

    for entry in request.ratings:
        if entry.risk_id not in risk_by_id:
            raise ValueError(f"Unknown risk id: {entry.risk_id}")
        if entry.risk_id in seen_ids:
            raise ValueError(f"Duplicate rating for risk id: {entry.risk_id}")
        seen_ids.add(entry.risk_id)
        ratings_by_id[entry.risk_id] = entry.rating

    category_order: list[str] = []
    category_counts: dict[str, dict[str, int]] = {}
    for risk in risks:
        if risk.category not in category_counts:
            category_counts[risk.category] = {"applicable": 0, "present": 0}
            category_order.append(risk.category)

        rating = ratings_by_id.get(risk.id)
        if rating in {RiskRating.PRESENT, RiskRating.NOT_PRESENT}:
            category_counts[risk.category]["applicable"] += 1
            if rating == RiskRating.PRESENT:
                category_counts[risk.category]["present"] += 1

    category_scores = [
        CategoryScore(
            category=category,
            applicable_risks=counts["applicable"],
            present_risks=counts["present"],
            score_pct=_round_pct(counts["present"], counts["applicable"]),
        )
        for category, counts in ((name, category_counts[name]) for name in category_order)
    ]

    total_applicable = sum(score.applicable_risks for score in category_scores)
    total_present = sum(score.present_risks for score in category_scores)
    thresholds = _top_tertile_thresholds(risks)

    flagged_high_risk: list[FlaggedRisk] = []
    recommendations: list[str] = []
    for risk in risks:
        rating = ratings_by_id.get(risk.id)
        if rating != RiskRating.PRESENT:
            continue
        threshold = thresholds[risk.source_paper]
        if risk.frequency_pct < threshold:
            continue
        related_cross_references = [
            cross_ref
            for cross_ref in cross_refs
            if cross_ref.a_risk == risk.id or cross_ref.b_risk == risk.id
        ]
        flagged_high_risk.append(
            FlaggedRisk(
                risk=risk,
                rating=rating,
                related_cross_references=related_cross_references,
            )
        )
        recommendations.append(_build_recommendation(risk))

    unrated_risks = [risk.id for risk in risks if risk.id not in ratings_by_id]

    return AssessmentResult(
        system_name=request.system_name,
        overall_score_pct=_round_pct(total_present, total_applicable),
        category_scores=category_scores,
        flagged_high_risk=flagged_high_risk,
        unrated_risks=unrated_risks,
        recommendations=recommendations,
    )
