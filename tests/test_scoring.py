from __future__ import annotations

from collections import Counter

from capra_pia.models import AssessmentRequest, CrossReference, Risk, RiskRating, RiskRatingEntry
from capra_pia.scoring import assess


def test_load_risks_returns_expected_counts(taxonomy) -> None:
    risks, cross_references = taxonomy

    assert len(risks) == 40
    assert len(cross_references) == 11
    assert Counter(risk.source_paper for risk in risks) == {"A": 19, "B": 21}


def test_assess_computes_category_scores_flags_and_unrated() -> None:
    risks = [
        Risk(
            id="A-C1-01",
            name="High frequency source A risk",
            category="Category One",
            source_paper="A",
            source_citation="Paper A",
            frequency_count=9,
            frequency_pct=90.0,
            definition="The most frequently cited source A issue.",
        ),
        Risk(
            id="A-C1-02",
            name="Lower frequency source A risk",
            category="Category One",
            source_paper="A",
            source_citation="Paper A",
            frequency_count=8,
            frequency_pct=80.0,
            definition="A different source A issue.",
        ),
        Risk(
            id="A-C1-03",
            name="Not present source A risk",
            category="Category One",
            source_paper="A",
            source_citation="Paper A",
            frequency_count=1,
            frequency_pct=10.0,
            definition="A source A issue that is absent in the system.",
        ),
        Risk(
            id="B-C2-01",
            name="Unrated source B risk",
            category="Category Two",
            source_paper="B",
            source_citation="Paper B",
            frequency_count=6,
            frequency_pct=60.0,
            definition="A source B issue left unrated in the request.",
        ),
    ]
    cross_references = [
        CrossReference(
            a_risk="A-C1-01",
            b_risk="B-C2-01",
            confidence="high",
            evidence_quote="These risks overlap in the synthetic fixture.",
        )
    ]
    request = AssessmentRequest(
        system_name="Synthetic System",
        ratings=[
            RiskRatingEntry(risk_id="A-C1-01", rating=RiskRating.PRESENT),
            RiskRatingEntry(risk_id="A-C1-02", rating=RiskRating.PRESENT),
            RiskRatingEntry(risk_id="A-C1-03", rating=RiskRating.NOT_PRESENT),
        ],
    )

    result = assess(request, risks, cross_references)

    assert result.system_name == "Synthetic System"
    assert result.overall_score_pct == 66.67
    assert [score.model_dump(mode="json") for score in result.category_scores] == [
        {
            "category": "Category One",
            "applicable_risks": 3,
            "present_risks": 2,
            "score_pct": 66.67,
        },
        {
            "category": "Category Two",
            "applicable_risks": 0,
            "present_risks": 0,
            "score_pct": 0.0,
        },
    ]
    assert [flag.risk.id for flag in result.flagged_high_risk] == ["A-C1-01"]
    assert result.flagged_high_risk[0].rating == RiskRating.PRESENT
    assert result.flagged_high_risk[0].related_cross_references == cross_references
    assert result.unrated_risks == ["B-C2-01"]
    assert result.recommendations == [
        "Prioritise controls for A-C1-01 (High frequency source A risk): "
        "The most frequently cited source A issue."
    ]


def test_assess_handles_empty_ratings_without_crashing() -> None:
    risks = [
        Risk(
            id="A-EMPTY-01",
            name="Only risk",
            category="Only Category",
            source_paper="A",
            source_citation="Paper A",
            frequency_count=1,
            frequency_pct=1.0,
            definition="A single taxonomy item.",
        )
    ]

    result = assess(
        AssessmentRequest(system_name="Empty Ratings System", ratings=[]),
        risks,
        [],
    )

    assert result.system_name == "Empty Ratings System"
    assert result.overall_score_pct == 0.0
    assert result.flagged_high_risk == []
    assert result.recommendations == []
    assert result.unrated_risks == ["A-EMPTY-01"]
    assert [score.model_dump(mode="json") for score in result.category_scores] == [
        {
            "category": "Only Category",
            "applicable_risks": 0,
            "present_risks": 0,
            "score_pct": 0.0,
        }
    ]
