from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from capra_pia.loader import load_risks
from capra_pia.models import AssessmentRequest, CrossReference, Risk, RiskRating, RiskRatingEntry
from capra_pia.scoring import assess


def _normalise_result(result) -> dict:
    return {
        "system_name": result.system_name,
        "overall_score_pct": result.overall_score_pct,
        "category_scores": [score.model_dump(mode="json") for score in result.category_scores],
        "flagged_high_risk": [
            {
                "risk_id": flagged.risk.id,
                "related_cross_reference_ids": [
                    f"{ref.a_risk}|{ref.b_risk}" for ref in flagged.related_cross_references
                ],
            }
            for flagged in result.flagged_high_risk
        ],
        "unrated_risks": result.unrated_risks,
        "recommendations": result.recommendations,
    }


def _run_js_assessment(repo_root: Path, payload: dict) -> dict:
    if shutil.which("node") is None:
        pytest.skip("node not available in this environment")

    harness_path = repo_root / "tests" / "._js_parity_harness.cjs"
    payload_path = repo_root / "tests" / "._js_parity_payload.json"

    harness_path.write_text(
        """
const fs = require("fs");
const scoring = require(process.argv[2]);
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const result = scoring.assess(payload.request, payload.risks, payload.crossRefs);
const normalised = {
  system_name: result.system_name,
  overall_score_pct: result.overall_score_pct,
  category_scores: result.category_scores,
  flagged_high_risk: result.flagged_high_risk.map((flagged) => ({
    risk_id: flagged.risk.id,
    related_cross_reference_ids: flagged.related_cross_references.map(
      (ref) => `${ref.a_risk}|${ref.b_risk}`
    ),
  })),
  unrated_risks: result.unrated_risks,
  recommendations: result.recommendations,
};
process.stdout.write(JSON.stringify(normalised));
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        completed = subprocess.run(
            [
                "node",
                str(harness_path),
                str(repo_root / "docs" / "js" / "scoring.js"),
                str(payload_path),
            ],
            capture_output=True,
            check=True,
            text=True,
            cwd=repo_root,
        )
    finally:
        harness_path.unlink(missing_ok=True)
        payload_path.unlink(missing_ok=True)

    return json.loads(completed.stdout)


def test_js_scoring_matches_python_for_synthetic_fixture(repo_root: Path) -> None:
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
            category_tag=None,
            note=None,
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
            category_tag=None,
            note=None,
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
            category_tag=None,
            note=None,
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
            category_tag=None,
            note=None,
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

    expected = _normalise_result(assess(request, risks, cross_references))
    payload = {
        "request": request.model_dump(mode="json"),
        "risks": [risk.model_dump(mode="json") for risk in risks],
        "crossRefs": [cross_reference.model_dump(mode="json") for cross_reference in cross_references],
    }

    assert _run_js_assessment(repo_root, payload) == expected


def test_js_scoring_matches_python_for_sample_ratings_file(repo_root: Path) -> None:
    risks, cross_references = load_risks(
        str(repo_root / "data" / "risks.yaml"),
        str(repo_root / "data" / "cross_references.yaml"),
    )
    payload = json.loads((repo_root / "examples" / "sample_ratings.json").read_text(encoding="utf-8"))
    request = AssessmentRequest(
        system_name=payload["system_name"],
        ratings=[
            RiskRatingEntry(risk_id=risk_id, rating=rating)
            for risk_id, rating in payload["ratings"].items()
        ],
    )

    expected = _normalise_result(assess(request, risks, cross_references))
    js_payload = {
        "request": request.model_dump(mode="json"),
        "risks": [risk.model_dump(mode="json") for risk in risks],
        "crossRefs": [cross_reference.model_dump(mode="json") for cross_reference in cross_references],
    }

    assert _run_js_assessment(repo_root, js_payload) == expected
