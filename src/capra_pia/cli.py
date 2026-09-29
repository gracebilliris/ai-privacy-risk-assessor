from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from capra_pia.loader import load_risks
from capra_pia.models import AssessmentRequest, RiskRatingEntry
from capra_pia.scoring import assess


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "data").is_dir():
            return parent
    raise RuntimeError("Could not locate repository root from cli.py")


def _data_dir() -> Path:
    configured = os.environ.get("CAPRA_PIA_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return _repo_root() / "data"


def _load_taxonomy():
    data_dir = _data_dir()
    return load_risks(str(data_dir / "risks.yaml"), str(data_dir / "cross_references.yaml"))


def _load_request(path: str) -> AssessmentRequest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Ratings JSON must be an object")

    system_name = payload.get("system_name", "Unnamed System")
    ratings_payload = payload.get("ratings", payload)
    if not isinstance(ratings_payload, dict):
        raise ValueError("Ratings JSON must contain a 'ratings' object")

    ratings = [
        RiskRatingEntry(risk_id=risk_id, rating=rating)
        for risk_id, rating in ratings_payload.items()
    ]
    return AssessmentRequest(system_name=system_name, ratings=ratings)


def _print_summary(result: Any) -> None:
    print("\nSummary")
    print(f"System: {result.system_name}")
    print(f"Overall score: {result.overall_score_pct:.2f}%")
    print("\nCategory scores")
    for score in result.category_scores:
        print(
            f"- {score.category}: {score.present_risks}/{score.applicable_risks} "
            f"present ({score.score_pct:.2f}%)"
        )

    print("\nFlagged high-risk items")
    if not result.flagged_high_risk:
        print("- None")
    else:
        for flagged in result.flagged_high_risk:
            print(
                f"- {flagged.risk.id} | {flagged.risk.name} | "
                f"{flagged.risk.source_paper} | {flagged.risk.frequency_pct:.2f}%"
            )

    print(f"\nUnrated risks: {len(result.unrated_risks)}")


def _cmd_list_risks(_: argparse.Namespace) -> int:
    risks, _ = _load_taxonomy()
    for risk in risks:
        print(f"{risk.id}\t{risk.name}\t{risk.category}\t{risk.source_paper}")
    return 0


def _cmd_assess(args: argparse.Namespace) -> int:
    risks, cross_refs = _load_taxonomy()
    request = _load_request(args.ratings_json)
    result = assess(request, risks, cross_refs)
    print(result.model_dump_json(indent=2))
    _print_summary(result)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("capra_pia.api:app", host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capra-pia")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-risks", help="List all risks")
    list_parser.set_defaults(func=_cmd_list_risks)

    assess_parser = subparsers.add_parser("assess", help="Assess a ratings JSON file")
    assess_parser.add_argument("ratings_json", help="Path to ratings JSON")
    assess_parser.set_defaults(func=_cmd_assess)

    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8000, type=int)
    serve_parser.set_defaults(func=_cmd_serve)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
