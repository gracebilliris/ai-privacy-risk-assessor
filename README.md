# ai-privacy-risk-assessor

**ai-privacy-risk-assessor** (`capra_pia`) is a free, standalone AI Privacy Impact Assessment tool grounded in a published, systematically reviewed taxonomy of AI and AI+Quantum (QAI) data privacy risks. It is designed as a lighter-weight companion to the broader [CAPRA prototype](https://github.com/gracebilliris/capra-prototype): small enough to install locally without Docker, but still usable by both AI agents (through a REST API and MCP server) and human reviewers (through a simple web form UI) who need a research-backed privacy-risk checklist and scoring workflow.

> **Research prototype.** This software is not production hardened. Its outputs are research artefacts for inspection, not certified compliance determinations, legal advice, or automated regulatory decisions.

## Quick Demo

[![Live Demo](https://img.shields.io/badge/Live%20Demo-client--side%20Pages-0a2540?style=flat-square)](https://gracebilliris.github.io/ai-privacy-risk-assessor/)

Open the static client-side demo at <https://gracebilliris.github.io/ai-privacy-risk-assessor/>. It runs entirely in the browser and is distinct from the full Python CLI/API/MCP tool documented below.

From the repository root, you can reproduce the CLI walkthrough with one command:

```bash
(.venv/bin/capra-pia list-risks | head -n 8) && echo && .venv/bin/capra-pia assess examples/sample_ratings.json
```

This repository includes the exact ratings file used in the demo at [`examples/sample_ratings.json`](examples/sample_ratings.json) and a real captured transcript at [`examples/demo_transcript.txt`](examples/demo_transcript.txt). An animated terminal asset was not generated in this environment; a maintainer can regenerate one locally with `asciinema`/`svg-term` or `vhs` if desired.

<details>
<summary>Captured transcript</summary>

```text
$ .venv/bin/capra-pia list-risks | head -n 8
A-DL-01	Unauthorised Data Access	Dataset-Level	A
A-DL-02	Unprotected Data Storage	Dataset-Level	A
A-DL-03	Unverified Data Sources	Dataset-Level	A
A-DL-04	Data Retention Failures	Dataset-Level	A
A-DL-05	Insufficient Anonymisation	Dataset-Level	A
A-ML-01	Membership Inference Attacks	Model-Level	A
A-ML-02	Model Inversion Attacks	Model-Level	A
A-ML-03	Training Data Memorisation	Model-Level	A

$ .venv/bin/capra-pia assess examples/sample_ratings.json
{
  "system_name": "CAPRA Demo System",
  "overall_score_pct": 66.67,
  "category_scores": [
    {
      "category": "Dataset-Level",
      "applicable_risks": 1,
      "present_risks": 1,
      "score_pct": 100.0
    },
    {
      "category": "Model-Level",
      "applicable_risks": 1,
      "present_risks": 1,
      "score_pct": 100.0
    },
    {
      "category": "Infrastructure-Level",
      "applicable_risks": 1,
      "present_risks": 0,
      "score_pct": 0.0
    },
    {
      "category": "Insider Threat",
      "applicable_risks": 1,
      "present_risks": 1,
      "score_pct": 100.0
    },
    {
      "category": "Governance & Risk Management",
      "applicable_risks": 2,
      "present_risks": 1,
      "score_pct": 50.0
    },
    {
      "category": "Privacy & Security Risk Assessment",
      "applicable_risks": 0,
      "present_risks": 0,
      "score_pct": 0.0
    },
    {
      "category": "Privacy & Security Controls Implementation",
      "applicable_risks": 0,
      "present_risks": 0,
      "score_pct": 0.0
    },
    {
      "category": "User-Centric Privacy Considerations",
      "applicable_risks": 0,
      "present_risks": 0,
      "score_pct": 0.0
    },
    {
      "category": "Continuous Monitoring & Improvement",
      "applicable_risks": 0,
      "present_risks": 0,
      "score_pct": 0.0
    }
  ],
  "flagged_high_risk": [
    {
      "risk": {
        "id": "A-DL-05",
        "name": "Insufficient Anonymisation",
        "category": "Dataset-Level",
        "source_paper": "A",
        "source_citation": "Billiris, Gill & Bandara (2025), Privacy in the Age of AI: A Taxonomy of Data Risks",
        "frequency_count": 35,
        "frequency_pct": 7.35,
        "definition": "Attempts to anonymise data fail, leaving information that can still identify individuals.\n",
        "category_tag": null,
        "note": null
      },
      "rating": "present",
      "related_cross_references": [
        {
          "a_risk": "A-DL-05",
          "b_risk": "B-CI-02",
          "confidence": "high",
          "evidence_quote": "B-CI-02 definition explicitly lists \"anonymisation\" (alongside data minimisation, consent tracking) as an example privacy-related control.\n"
        }
      ]
    },
    {
      "risk": {
        "id": "A-ML-03",
        "name": "Training Data Memorisation",
        "category": "Model-Level",
        "source_paper": "A",
        "source_citation": "Billiris, Gill & Bandara (2025), Privacy in the Age of AI: A Taxonomy of Data Risks",
        "frequency_count": 42,
        "frequency_pct": 8.82,
        "definition": "AI models unintentionally \"remember\" exact sensitive information from the training dataset in their outputs.\n",
        "category_tag": null,
        "note": null
      },
      "rating": "present",
      "related_cross_references": [
        {
          "a_risk": "A-ML-03",
          "b_risk": "B-RA-02",
          "confidence": "high",
          "evidence_quote": "B-RA-02 definition names \"memorisation, leakage via outputs, or weak training data protections\" as examples of this broader risk.\n"
        }
      ]
    },
    {
      "risk": {
        "id": "A-IT-02",
        "name": "Human Error",
        "category": "Insider Threat",
        "source_paper": "A",
        "source_citation": "Billiris, Gill & Bandara (2025), Privacy in the Age of AI: A Taxonomy of Data Risks",
        "frequency_count": 45,
        "frequency_pct": 9.45,
        "definition": "Accidental mistakes by individuals, such as sending data to wrong recipients or mismanaging sensitive files.\n",
        "category_tag": null,
        "note": "Single most cited risk factor across the whole taxonomy."
      },
      "rating": "present",
      "related_cross_references": []
    },
    {
      "risk": {
        "id": "B-GV-01",
        "name": "AI Governance & Privacy Compliance Risks",
        "category": "Governance & Risk Management",
        "source_paper": "B",
        "source_citation": "Billiris, Gill & Bandara (2025), A Taxonomy of Data Risks in AI and Quantum Computing (QAI) — A Systematic Review",
        "frequency_count": 50,
        "frequency_pct": 7.0,
        "definition": "Risks associated with the alignment of AI governance frameworks with privacy compliance standards, leading to inadequate privacy protections.\n",
        "category_tag": "P",
        "note": null
      },
      "rating": "present",
      "related_cross_references": []
    }
  ],
  "unrated_risks": [
    "A-DL-01",
    "A-DL-02",
    "A-DL-03",
    "A-DL-04",
    "A-ML-01",
    "A-ML-02",
    "A-ML-04",
    "A-ML-05",
    "A-IL-01",
    "A-IL-02",
    "A-IL-03",
    "A-IL-05",
    "A-IT-01",
    "A-IT-03",
    "A-IT-04",
    "B-GV-03",
    "B-GV-04",
    "B-RA-02",
    "B-RA-03",
    "B-RA-04",
    "B-CI-01",
    "B-CI-02",
    "B-CI-03",
    "B-CI-04",
    "B-UC-01",
    "B-UC-02",
    "B-UC-03",
    "B-UC-04",
    "B-UC-05",
    "B-CM-01",
    "B-CM-02",
    "B-CM-03",
    "B-CM-04"
  ],
  "recommendations": [
    "Prioritise controls for A-DL-05 (Insufficient Anonymisation): Attempts to anonymise data fail, leaving information that can still identify individuals.",
    "Prioritise controls for A-ML-03 (Training Data Memorisation): AI models unintentionally \"remember\" exact sensitive information from the training dataset in their outputs.",
    "Prioritise controls for A-IT-02 (Human Error): Accidental mistakes by individuals, such as sending data to wrong recipients or mismanaging sensitive files.",
    "Prioritise controls for B-GV-01 (AI Governance & Privacy Compliance Risks): Risks associated with the alignment of AI governance frameworks with privacy compliance standards, leading to inadequate privacy protections."
  ]
}

Summary
System: CAPRA Demo System
Overall score: 66.67%

Category scores
- Dataset-Level: 1/1 present (100.00%)
- Model-Level: 1/1 present (100.00%)
- Infrastructure-Level: 0/1 present (0.00%)
- Insider Threat: 1/1 present (100.00%)
- Governance & Risk Management: 1/2 present (50.00%)
- Privacy & Security Risk Assessment: 0/0 present (0.00%)
- Privacy & Security Controls Implementation: 0/0 present (0.00%)
- User-Centric Privacy Considerations: 0/0 present (0.00%)
- Continuous Monitoring & Improvement: 0/0 present (0.00%)

Flagged high-risk items
- A-DL-05 | Insufficient Anonymisation | A | 7.35%
- A-ML-03 | Training Data Memorisation | A | 8.82%
- A-IT-02 | Human Error | A | 9.45%
- B-GV-01 | AI Governance & Privacy Compliance Risks | B | 7.00%

Unrated risks: 33
```

</details>

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

Add `--verbose` to also show each risk's definition and its assessment guiding question:

```bash
capra-pia list-risks --verbose
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

A separate fully static, client-side-only demo suitable for GitHub Pages is provided in [`docs/`](docs/) and published at <https://gracebilliris.github.io/ai-privacy-risk-assessor/>.

## Repository layout

This repository follows the structure defined in [`CORE_CONTRACT.md`](CORE_CONTRACT.md):

```text
ai-privacy-risk-assessor/
├── data/
│   ├── risks.yaml
│   ├── cross_references.yaml
│   └── MERGE_LOG.md
├── docs/
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── data/
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
│   ├── test_mcp.py
│   └── test_js_parity.py
├── README.md
├── CITATION.cff
└── pyproject.toml
```

## Citation

If you use this software artefact, please cite the repository metadata in [`CITATION.cff`](CITATION.cff) and the two underlying taxonomy papers listed above.

## Licence

Released under the [MIT License](LICENSE).
