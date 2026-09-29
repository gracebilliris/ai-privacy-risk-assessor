from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from pydantic import ValidationError

from capra_pia.loader import load_risks
from capra_pia.models import AssessmentRequest, CrossReference, Risk, RiskRatingEntry
from capra_pia.scoring import assess


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


def _risk_to_dict(risk: Risk) -> dict[str, Any]:
    return risk.model_dump(mode="json")


RISKS, CROSS_REFERENCES = _load_taxonomy()
RISK_BY_ID = {risk.id: risk for risk in RISKS}


server = MCPServer(
    name="capra-pia",
    title="CAPRA Privacy Risk Assessor",
    description="MCP tools for exploring the CAPRA AI/QAI privacy risk taxonomy and scoring assessments.",
    instructions=(
        "Use these tools to inspect the CAPRA privacy risk taxonomy and assess "
        "ratings against the published research rubric. This is a research "
        "prototype, not a certified compliance tool."
    ),
    version="0.1.0",
)
mcp = server


@server.tool(
    description="Return all privacy risks from the CAPRA taxonomy as JSON-serialisable dictionaries.",
    structured_output=True,
)
def list_privacy_risks() -> list[dict[str, Any]]:
    return [_risk_to_dict(risk) for risk in RISKS]


@server.tool(
    description="Return one privacy risk by id, or an error message if the risk does not exist.",
    structured_output=True,
)
def get_risk(risk_id: str) -> dict[str, Any]:
    risk = RISK_BY_ID.get(risk_id)
    if risk is None:
        return {"error": f"Risk '{risk_id}' not found"}
    return _risk_to_dict(risk)


@server.tool(
    description=(
        "Build an assessment request from a system name and risk-id-to-rating "
        "mapping, then return the scored assessment result."
    ),
    structured_output=True,
)
def assess_privacy_risk(system_name: str, ratings: dict[str, str]) -> dict[str, Any]:
    try:
        request = AssessmentRequest(
            system_name=system_name,
            ratings=[
                RiskRatingEntry(risk_id=risk_id, rating=rating)
                for risk_id, rating in ratings.items()
            ],
        )
        result = assess(request, RISKS, CROSS_REFERENCES)
    except (ValidationError, ValueError) as exc:
        return {"error": str(exc)}

    return result.model_dump(mode="json")


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
