from __future__ import annotations

import asyncio

from capra_pia import mcp_server


def test_mcp_tools_are_registered() -> None:
    tool_names = {tool.name for tool in asyncio.run(mcp_server.server.list_tools())}

    assert {"list_privacy_risks", "get_risk", "assess_privacy_risk"} <= tool_names


def test_list_privacy_risks_returns_full_taxonomy() -> None:
    payload = mcp_server.list_privacy_risks()

    assert isinstance(payload, list)
    assert len(payload) == 40
    assert payload[0]["id"]
    assert payload[0]["source_paper"] in {"A", "B"}


def test_get_risk_returns_expected_payloads() -> None:
    valid = mcp_server.get_risk("A-DL-01")
    missing = mcp_server.get_risk("NOPE-00")

    assert valid["id"] == "A-DL-01"
    assert missing == {"error": "Risk 'NOPE-00' not found"}


def test_assess_privacy_risk_returns_structured_result() -> None:
    payload = mcp_server.assess_privacy_risk(
        system_name="MCP smoke test",
        ratings={
            "A-ML-03": "present",
            "A-DL-01": "not_present",
            "B-GV-01": "present",
        },
    )

    assert payload["system_name"] == "MCP smoke test"
    assert payload["overall_score_pct"] == 66.67
    assert isinstance(payload["category_scores"], list)
    assert isinstance(payload["flagged_high_risk"], list)
    assert len(payload["unrated_risks"]) == 37
    assert {item["risk"]["id"] for item in payload["flagged_high_risk"]} >= {
        "A-ML-03",
        "B-GV-01",
    }
