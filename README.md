# ai-privacy-risk-assessor

**ai-privacy-risk-assessor** (`capra_pia`) is a free, standalone AI Privacy Impact Assessment tool grounded in a published, systematically reviewed taxonomy of AI and AI+Quantum (QAI) data privacy risks. It is designed as a lighter-weight companion to the broader [CAPRA prototype](https://github.com/gracebilliris/capra-prototype): small enough to install locally without Docker, but still usable by both AI agents (through a REST API and MCP server) and human reviewers (through a simple web form UI) who need a research-backed privacy-risk checklist and scoring workflow.

> **Research prototype.** This software is not production hardened. Its outputs are research artefacts for inspection, not certified compliance determinations, legal advice, or automated regulatory decisions.

## Evidence base

This tool implements a combined evidence base drawn from two related published taxonomies:

1. **Billiris, G., Gill, A., & Bandara, M. (2025). _Privacy in the Age of AI: A Taxonomy of Data Risks_. arXiv:2510.02357.**
   - Paper A contributes **19 risks across 4 categories**.
2. **Billiris, G., Gill, A., & Bandara, M. (2025). _A Taxonomy of Data Risks in AI and Quantum Computing (QAI) — A Systematic Review_. arXiv:2509.20418.**
   - Paper B was published with **22 risks across 5 categories**, but this tool uses **21 risks** after consolidating one duplicate table row.

In this repository, the working taxonomy therefore contains **40 risks total**: **19 from Paper A + 21 from Paper B**. The consolidation rationale is documented in [`data/MERGE_LOG.md`](data/MERGE_LOG.md). The relationship between the two taxonomies is documented in [`data/cross_references.yaml`](data/cross_references.yaml): they classify risks along different axes, so they should not be treated as simple duplicates of one another.

## Relationship to CAPRA

This repository is the lightweight companion to the full [CAPRA prototype](https://github.com/gracebilliris/capra-prototype), which demonstrates a broader multi-layer, multi-agent privacy-risk assessment architecture. By contrast, **ai-privacy-risk-assessor** focuses on a portable Python package with:

- a command-line interface;
- a FastAPI-based REST API;
- an MCP server for agent tooling; and
- a small web form for human-driven assessments.

Both repositories draw on the same underlying research programme, but this one is intentionally simpler to run and easier to embed into local tooling, scripts, and AI-agent workflows.

## Installation

Requirements:

- Python 3.10+
- `pip`

Install in editable mode from the repository root:

```bash
pip install -e .
```

## CLI usage

List the available risks:

```bash
capra-pia list-risks
```

Assess a system from a JSON ratings file:

```bash
capra-pia assess ratings.json
```

A minimal `ratings.json` file can use `{risk_id: rating}` pairs, for example:

```json
{
  "A-DL-01": "present",
  "A-DL-02": "not_present",
  "A-ML-03": "present",
  "B-CI-01": "unknown",
  "B-UC-03": "not_applicable"
}
```

## REST API

Start the API with the packaged CLI wrapper:

```bash
capra-pia serve
```

Or run it directly with Uvicorn:

```bash
uvicorn capra_pia.api:app --reload
```

Once running, the key endpoints are:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/risks` | Return the full list of risks |
| `GET` | `/risks/{id}` | Return one risk by ID |
| `GET` | `/categories` | Return category names and risk counts |
| `POST` | `/assess` | Submit an assessment request and receive scores, flagged risks, and recommendations |
| `GET` | `/health` | Return a simple health check |

Example requests:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risks
curl http://127.0.0.1:8000/risks/A-ML-03
```

Example assessment request:

```bash
curl -X POST http://127.0.0.1:8000/assess \
  -H 'Content-Type: application/json' \
  -d '{
    "system_name": "Example AI system",
    "ratings": [
      {"risk_id": "A-DL-01", "rating": "present"},
      {"risk_id": "A-ML-03", "rating": "present"},
      {"risk_id": "B-CI-01", "rating": "not_present"}
    ]
  }'
```

## MCP server

The repository also exposes the taxonomy through an MCP server so MCP-capable clients such as GitHub Copilot can call it as a tool.

A typical stdio registration points the MCP host at the Python module:

```json
{
  "mcpServers": {
    "capra-pia": {
      "command": "python",
      "args": ["-m", "capra_pia.mcp_server"],
      "cwd": "/Users/gracebilliris/Projects/ai-privacy-risk-assessor"
    }
  }
}
```

The MCP server exposes these tools:

- `list_privacy_risks()`
- `get_risk(risk_id)`
- `assess_privacy_risk(system_name, ratings)`

This makes the same evidence base available to automated agent workflows without requiring the agent to scrape files or call the HTTP API.

## Web form UI

When the API is running (`capra-pia serve` or `uvicorn capra_pia.api:app`), the web form UI is mounted directly into the same app. Open it in a browser at:

- <http://127.0.0.1:8000/ui/>

The form presents the risks grouped by category, lets a reviewer select ratings for each risk, submits the assessment to the API, and renders the resulting report for human review.

## Repository layout

This repository follows the structure defined in [`CORE_CONTRACT.md`](CORE_CONTRACT.md):

```text
ai-privacy-risk-assessor/
├── data/
│   ├── risks.yaml
│   ├── cross_references.yaml
│   └── MERGE_LOG.md
├── src/capra_pia/
│   ├── __init__.py
│   ├── models.py
│   ├── loader.py
│   ├── scoring.py
│   ├── cli.py
│   ├── api.py
│   ├── mcp_server.py
│   └── web/
│       ├── __init__.py
│       ├── routes.py
│       ├── templates/
│       └── static/
├── tests/
│   ├── test_scoring.py
│   ├── test_api.py
│   └── test_mcp.py
├── README.md
├── CITATION.cff
└── pyproject.toml
```

## Citation

If you use this software artefact, please cite the repository metadata in [`CITATION.cff`](CITATION.cff) and the two underlying taxonomy papers listed above.

## Licence

Released under the [MIT License](LICENSE).
