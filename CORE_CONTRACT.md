# CORE_CONTRACT.md — shared interface for all sub-agents

This defines the module boundaries and interfaces every sub-agent must build
against, so work can proceed in parallel without merge conflicts. **Do not
edit files outside your assigned scope.** If the contract itself needs to
change, flag it rather than silently deviating.

## Repo layout (own only your listed files)

```
ai-privacy-risk-assessor/
├── data/
│   ├── risks.yaml              # DONE — canonical rubric, do not edit
│   ├── cross_references.yaml   # DONE — do not edit
│   └── MERGE_LOG.md            # DONE — do not edit
├── src/capra_pia/
│   ├── __init__.py
│   ├── models.py                # OWNER: developer-core
│   ├── loader.py                 # OWNER: developer-core
│   ├── scoring.py                # OWNER: developer-core
│   ├── cli.py                    # OWNER: developer-core
│   ├── api.py                    # OWNER: developer-api
│   ├── mcp_server.py              # OWNER: developer-mcp
│   ├── web/
│   │   ├── __init__.py           # OWNER: developer-web
│   │   ├── routes.py             # OWNER: developer-web
│   │   ├── templates/*.html      # OWNER: developer-web
│   │   └── static/*.css          # OWNER: developer-web
├── tests/
│   ├── test_scoring.py           # OWNER: qa-tester
│   ├── test_api.py               # OWNER: qa-tester
│   └── test_mcp.py               # OWNER: qa-tester
├── README.md                     # OWNER: docs-writer
├── CITATION.cff                  # OWNER: docs-writer
└── pyproject.toml                # DONE
```

## Core data model (`src/capra_pia/models.py`) — developer-core owns, everyone
else imports from it, nobody else redefines it

```python
from enum import Enum
from pydantic import BaseModel

class RiskRating(str, Enum):
    PRESENT = "present"
    NOT_PRESENT = "not_present"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

class Risk(BaseModel):
    id: str                  # e.g. "A-DL-01" or "B-CI-02"
    name: str
    category: str            # e.g. "Dataset-Level"
    source_paper: str        # "A" or "B"
    source_citation: str     # full citation string
    frequency_count: int
    frequency_pct: float
    definition: str
    assessment_prompt: str    # guiding yes/no question derived from definition, for UI display
    category_tag: str | None = None   # "P" / "S", Paper B only
    note: str | None = None

class CrossReference(BaseModel):
    a_risk: str
    b_risk: str
    confidence: str          # "high" | "medium"
    evidence_quote: str

class RiskRatingEntry(BaseModel):
    risk_id: str
    rating: RiskRating
    evidence_note: str | None = None

class AssessmentRequest(BaseModel):
    system_name: str
    ratings: list[RiskRatingEntry]

class CategoryScore(BaseModel):
    category: str
    applicable_risks: int
    present_risks: int
    score_pct: float          # present / applicable * 100

class FlaggedRisk(BaseModel):
    risk: Risk
    rating: RiskRating
    related_cross_references: list[CrossReference] = []

class AssessmentResult(BaseModel):
    system_name: str
    overall_score_pct: float
    category_scores: list[CategoryScore]
    flagged_high_risk: list[FlaggedRisk]
    unrated_risks: list[str]   # risk ids present in taxonomy, absent from request
    recommendations: list[str]
```

## `src/capra_pia/loader.py` (developer-core)

```python
def load_risks(risks_path: str, cross_refs_path: str) -> tuple[list[Risk], list[CrossReference]]:
    """Parse data/risks.yaml and data/cross_references.yaml into typed models."""
```

## `src/capra_pia/scoring.py` (developer-core)

```python
def assess(request: AssessmentRequest, risks: list[Risk], cross_refs: list[CrossReference]) -> AssessmentResult:
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
```

## `src/capra_pia/cli.py` (developer-core)

- `capra-pia list-risks [--verbose]` — print all risks (id, name, category, source); `--verbose` also prints each risk's definition and assessment guiding question.
- `capra-pia assess <ratings.json>` — load a JSON file of
  `{risk_id: rating}` pairs, run `assess()`, print JSON + a human-readable
  summary table.
- `capra-pia serve` — thin wrapper that runs the API (`uvicorn capra_pia.api:app`).

## `src/capra_pia/api.py` (developer-api) — imports `models`, `loader`,
`scoring` from developer-core's modules; does not redefine them.

FastAPI app, endpoints:
- `GET /risks` → list[Risk]
- `GET /risks/{risk_id}` → Risk
- `GET /categories` → list of category names + risk counts
- `POST /assess` → body: AssessmentRequest → returns AssessmentResult
- `GET /health` → `{"status": "ok"}`

Load `data/risks.yaml` / `data/cross_references.yaml` once at startup
(module-level, via `loader.load_risks`), relative to repo root (use a
`DATA_DIR` env var with a sane default, do not hardcode an absolute path).

## `src/capra_pia/mcp_server.py` (developer-mcp) — imports `models`,
`loader`, `scoring` directly (does NOT call the HTTP API — call the Python
functions directly to avoid a network dependency)

Expose MCP tools:
- `list_privacy_risks()` → same as `GET /risks`
- `get_risk(risk_id: str)` → same as `GET /risks/{id}`
- `assess_privacy_risk(system_name: str, ratings: dict)` → runs `scoring.assess()`
  and returns the JSON-serialisable result, so any MCP-capable AI agent
  (e.g. Copilot) can call this tool directly during a conversation.

Use the official `mcp` Python SDK (stdio transport is sufficient for v1).

## `src/capra_pia/web/` (developer-web) — imports `models`, calls the API
over HTTP (use `httpx`), does not import `scoring`/`loader` directly, so the
web UI is a genuine client of the API rather than a second core implementation

- `GET /` (mounted into the FastAPI app by developer-api, or run as its own
  small FastAPI/Starlette app during dev — confirm mounting approach with a
  comment in `web/routes.py` if you deviate) — renders a form listing all
  risks grouped by category with a select per risk (present/not
  present/n/a), submits to `/assess`, renders the returned `AssessmentResult`
  as a simple report page (category scores as a bar/table, flagged risks
  list with definitions and citations).
- Keep templates minimal (no JS framework), plain HTML + a little CSS.

## Tests (qa-tester) — owns `tests/`, does not edit `src/`

- `test_scoring.py`: unit tests for `loader.load_risks` (correct counts: 19
  Paper A + 21 Paper B = 40) and `scoring.assess` (category math, flagging
  logic, unrated risk detection) using small synthetic rating fixtures.
- `test_api.py`: FastAPI TestClient tests for all endpoints, including a
  round-trip `/assess` call.
- `test_mcp.py`: smoke test that MCP tools are registered and callable with
  a minimal in-process call (not a full stdio transport test).
- Report pass/fail back to the orchestrator, do not silently skip failures.

## Docs (docs-writer) — owns `README.md`, `CITATION.cff`

- README: purpose, evidence base (cite Papers A & B), install/run
  instructions for CLI, API, MCP server, and web UI, plus a note on the
  `MERGE_LOG.md`/`cross_references.yaml` consolidation decisions (link to
  `data/MERGE_LOG.md`) and the "research artefact, not a certified
  compliance tool" caveat (mirror `capra-prototype`'s existing caveat tone).
- `CITATION.cff`: cff-version 1.2.0, cite Papers A and B as the
  preferred/related citations plus this software artefact, same style as
  `capra-prototype/CITATION.cff` (MIT licence, Grace Billiris author, ORCID
  `0009-0001-3122-9985`).

## Cross-cutting rules for every sub-agent

1. Only touch files in your owned scope above. If you need a shared file
   changed, stop and report back rather than editing it.
2. No fabricated risk content — `data/risks.yaml` and
   `data/cross_references.yaml` are the single source of truth; don't invent
   additional risks, scores, or citations.
3. Keep the "research prototype, not a certified compliance tool" caveat
   consistent with `capra-prototype`'s tone (see its README) wherever the
   tool's output is described.
4. Use Python 3.10+, type hints, and keep functions small and testable.
