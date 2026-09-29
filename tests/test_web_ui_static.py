from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
from typing import Iterator

from playwright.sync_api import Page, expect, sync_playwright

from capra_pia.loader import load_risks
from capra_pia.models import AssessmentRequest, RiskRatingEntry
from capra_pia.scoring import assess


def _sample_payload(repo_root: Path) -> dict:
    return json.loads((repo_root / "examples" / "sample_ratings.json").read_text(encoding="utf-8"))


def _sample_expectations(repo_root: Path) -> tuple[float, list[str], int]:
    risks, cross_references = load_risks(
        str(repo_root / "data" / "risks.yaml"),
        str(repo_root / "data" / "cross_references.yaml"),
    )
    payload = _sample_payload(repo_root)
    request = AssessmentRequest(
        system_name=payload["system_name"],
        ratings=[
            RiskRatingEntry(risk_id=risk_id, rating=rating)
            for risk_id, rating in payload["ratings"].items()
        ],
    )
    result = assess(request, risks, cross_references)

    flagged_ids = [item.risk.id for item in result.flagged_high_risk]
    assert result.overall_score_pct == 66.67
    assert flagged_ids == ["A-DL-05", "A-ML-03", "A-IT-02", "B-GV-01"]
    assert len(result.unrated_risks) == 33
    return result.overall_score_pct, flagged_ids, len(result.unrated_risks)


def _file_fetch_shim(repo_root: Path) -> str:
    risks = json.loads((repo_root / "docs" / "data" / "risks.json").read_text(encoding="utf-8"))
    cross_references = json.loads(
        (repo_root / "docs" / "data" / "cross_references.json").read_text(encoding="utf-8")
    )
    fixtures = {
        "data/risks.json": risks,
        "data/cross_references.json": cross_references,
    }
    return f"""
const __capraFixtures = {json.dumps(fixtures)};
const __capraNativeFetch = globalThis.fetch ? globalThis.fetch.bind(globalThis) : null;
globalThis.fetch = async (input, init) => {{
  const url = typeof input === "string" ? input : (input && "url" in input ? input.url : String(input));
  for (const [suffix, payload] of Object.entries(__capraFixtures)) {{
    if (url.endsWith(suffix)) {{
      return new Response(JSON.stringify(payload), {{
        status: 200,
        headers: {{ "Content-Type": "application/json" }}
      }});
    }}
  }}
  if (!__capraNativeFetch) {{
    throw new Error(`Unexpected fetch target: ${{url}}`);
  }}
  return __capraNativeFetch(input, init);
}};
"""


@contextmanager
def _static_page(repo_root: Path) -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--allow-file-access-from-files"])
        page = browser.new_page()
        page.add_init_script(_file_fetch_shim(repo_root))
        page.goto((repo_root / "docs" / "index.html").resolve().as_uri(), wait_until="load")
        expect(page.locator("#assessment-form-sections .risk-card").first).to_be_visible(timeout=10_000)
        try:
            yield page
        finally:
            browser.close()


def test_static_demo_assesses_sample_ratings(repo_root: Path) -> None:
    expected_score, expected_flagged_ids, expected_unrated_count = _sample_expectations(repo_root)
    payload = _sample_payload(repo_root)
    with _static_page(repo_root) as page:
        page.locator("#system-name").fill(payload["system_name"])
        for risk_id, rating in payload["ratings"].items():
            page.locator(f"#rating__{risk_id}").select_option(rating)

        page.get_by_role("button", name="Assess").click()

        expect(page.locator("#results")).to_be_visible(timeout=10_000)
        expect(page.locator("#ui-error")).to_be_hidden()
        expect(page.locator("#overall-score")).to_have_text(f"{expected_score:.2f}%")
        expect(page.locator("#flagged-count")).to_have_text(str(len(expected_flagged_ids)))
        expect(page.locator("#unrated-count")).to_have_text(str(expected_unrated_count))
        expect(page.locator("#summary-output")).to_contain_text("Overall score: 66.67%")
        expect(page.locator("#summary-output")).to_contain_text("Unrated risks: 33")

        flagged_headings = page.locator("#flagged-items h3")
        expect(flagged_headings).to_have_count(len(expected_flagged_ids))
        flagged_text = "\n".join(flagged_headings.all_text_contents())
        for risk_id in expected_flagged_ids:
            assert risk_id in flagged_text


def test_static_demo_handles_zero_ratings_without_crashing(repo_root: Path, loaded_risks) -> None:
    with _static_page(repo_root) as page:
        page.locator("#system-name").fill("Static UI zero ratings")
        page.get_by_role("button", name="Assess").click()

        expect(page.locator("#results")).to_be_visible(timeout=10_000)
        expect(page.locator("#ui-error")).to_be_hidden()
        expect(page.locator("#overall-score")).to_have_text("0.00%")
        expect(page.locator("#flagged-count")).to_have_text("0")
        expect(page.locator("#unrated-count")).to_have_text(str(len(loaded_risks)))
        expect(page.locator("#summary-output")).to_contain_text("System: Static UI zero ratings")
        expect(page.locator("#summary-output")).to_contain_text(f"Unrated risks: {len(loaded_risks)}")
