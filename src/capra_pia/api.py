from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from capra_pia.loader import load_risks
from capra_pia.models import AssessmentRequest, AssessmentResult, CrossReference, Risk
from capra_pia.scoring import assess
from capra_pia.web import router as web_router


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _data_dir() -> Path:
    configured = os.environ.get("CAPRA_PIA_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return _default_data_dir()


def _load_taxonomy() -> tuple[list[Risk], list[CrossReference]]:
    data_dir = _data_dir()
    return load_risks(str(data_dir / "risks.yaml"), str(data_dir / "cross_references.yaml"))


RISKS, CROSS_REFERENCES = _load_taxonomy()
RISK_BY_ID = {risk.id: risk for risk in RISKS}


app = FastAPI(title="CAPRA PIA API")
app.include_router(web_router, prefix="/ui")


@app.get("/risks", response_model=list[Risk])
def list_risks() -> list[Risk]:
    return RISKS


@app.get("/risks/{risk_id}", response_model=Risk)
def get_risk(risk_id: str) -> Risk:
    risk = RISK_BY_ID.get(risk_id)
    if risk is None:
        raise HTTPException(status_code=404, detail=f"Risk '{risk_id}' not found")
    return risk


@app.get("/categories")
def list_categories() -> list[dict[str, Any]]:
    categories: OrderedDict[tuple[str, str], int] = OrderedDict()
    for risk in RISKS:
        key = (risk.category, risk.source_paper)
        categories[key] = categories.get(key, 0) + 1

    return [
        {
            "category": category,
            "source_paper": source_paper,
            "risk_count": risk_count,
        }
        for (category, source_paper), risk_count in categories.items()
    ]


@app.post("/assess", response_model=AssessmentResult)
def assess_risks(request: AssessmentRequest) -> AssessmentResult:
    try:
        return assess(request, RISKS, CROSS_REFERENCES)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
