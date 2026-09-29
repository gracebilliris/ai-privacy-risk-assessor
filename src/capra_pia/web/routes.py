from __future__ import annotations

# Integration note:
# Include this router from the main FastAPI app with `app.include_router(router, prefix="/ui")`.
# The router already mounts its local static assets at `/static`, so once included
# with that prefix the UI will be available at `/ui/` and its stylesheet at
# `/ui/static/style.css`.

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from capra_pia.models import AssessmentResult, Risk

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()
router.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _api_base_url() -> str:
    return os.environ.get("CAPRA_PIA_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


async def _get_json(path: str) -> Any:
    url = f"{_api_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach CAPRA PIA API at {url}: {exc}",
        ) from exc
    return response.json()


async def _post_json(path: str, payload: dict[str, Any]) -> Any:
    url = f"{_api_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach CAPRA PIA API at {url}: {exc}",
        ) from exc

    if response.status_code >= 400:
        detail = response.text
        try:
            body = response.json()
        except ValueError:
            body = None
        if isinstance(body, dict) and body.get("detail"):
            detail = str(body["detail"])
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


async def _fetch_risks() -> list[Risk]:
    payload = await _get_json("/risks")
    return [Risk.model_validate(item) for item in payload]


def _group_risks(risks: list[Risk]) -> OrderedDict[str, list[Risk]]:
    grouped: OrderedDict[str, list[Risk]] = OrderedDict()
    for risk in risks:
        grouped.setdefault(risk.category, []).append(risk)
    return grouped


def _build_ratings_payload(form_data: Any, risks: list[Risk]) -> list[dict[str, Any]]:
    ratings: list[dict[str, Any]] = []
    for risk in risks:
        rating_value = str(form_data.get(f"rating__{risk.id}", "unknown")).strip() or "unknown"
        evidence_note = str(form_data.get(f"evidence__{risk.id}", "")).strip() or None
        ratings.append(
            {
                "risk_id": risk.id,
                "rating": rating_value,
                "evidence_note": evidence_note,
            }
        )
    return ratings


def _build_form_context(
    request: Request,
    risks: list[Risk],
    *,
    system_name: str = "",
    error_message: str | None = None,
    selected_ratings: dict[str, str] | None = None,
    evidence_notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "request": request,
        "grouped_risks": _group_risks(risks),
        "system_name": system_name,
        "error_message": error_message,
        "selected_ratings": selected_ratings or {},
        "evidence_notes": evidence_notes or {},
    }


@router.get("/", response_class=HTMLResponse, name="ui_form")
async def show_form(request: Request) -> HTMLResponse:
    risks = await _fetch_risks()
    return templates.TemplateResponse(request, "form.html", _build_form_context(request, risks))


@router.post("/submit", response_class=HTMLResponse, name="ui_submit")
async def submit_assessment(request: Request) -> HTMLResponse:
    form_data = await request.form()
    system_name = str(form_data.get("system_name", "")).strip()
    risks = await _fetch_risks()

    selected_ratings = {
        risk.id: str(form_data.get(f"rating__{risk.id}", "unknown")).strip() or "unknown"
        for risk in risks
    }
    evidence_notes = {
        risk.id: str(form_data.get(f"evidence__{risk.id}", "")).strip()
        for risk in risks
        if str(form_data.get(f"evidence__{risk.id}", "")).strip()
    }

    payload = {
        "system_name": system_name,
        "ratings": _build_ratings_payload(form_data, risks),
    }

    try:
        response_payload = await _post_json("/assess", payload)
        result = AssessmentResult.model_validate(response_payload)
    except HTTPException as exc:
        context = _build_form_context(
            request,
            risks,
            system_name=system_name,
            error_message=str(exc.detail),
            selected_ratings=selected_ratings,
            evidence_notes=evidence_notes,
        )
        return templates.TemplateResponse(request, "form.html", context, status_code=exc.status_code)

    risk_lookup = {risk.id: risk for risk in risks}
    unrated_risk_details = [risk_lookup[risk_id] for risk_id in result.unrated_risks if risk_id in risk_lookup]

    context = {
        "request": request,
        "result": result,
        "unrated_risk_details": unrated_risk_details,
    }
    return templates.TemplateResponse(request, "report.html", context)
