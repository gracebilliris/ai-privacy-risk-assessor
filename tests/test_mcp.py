from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

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


def test_assess_privacy_risk_returns_error_for_unknown_risk_id() -> None:
    payload = mcp_server.assess_privacy_risk(
        system_name="MCP invalid risk test",
        ratings={"NOPE-00": "present"},
    )

    assert payload == {"error": "Unknown risk id: NOPE-00"}


def test_stdio_transport_real_client_server_round_trip(repo_root: Path) -> None:
    """Drives the actual MCP server subprocess over the real stdio protocol
    (not just calling the plain Python functions) using the official mcp
    client, to catch transport/registration bugs the direct-call tests above
    cannot see."""
    mcp_client = pytest.importorskip("mcp")
    from mcp import ClientSession  # noqa: PLC0415
    from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: PLC0415

    async def _round_trip() -> tuple[set[str], dict, dict]:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "capra_pia.mcp_server"],
            cwd=str(repo_root),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()

                get_risk_result = await session.call_tool(
                    "get_risk", {"risk_id": "A-DL-01"}
                )
                assess_result = await session.call_tool(
                    "assess_privacy_risk",
                    {
                        "system_name": "stdio round trip",
                        "ratings": {"A-ML-03": "present"},
                    },
                )
                return (
                    {tool.name for tool in tools.tools},
                    json.loads(get_risk_result.content[0].text),
                    json.loads(assess_result.content[0].text),
                )

    tool_names, risk_payload, assess_payload = asyncio.run(
        asyncio.wait_for(_round_trip(), timeout=20)
    )

    assert {"list_privacy_risks", "get_risk", "assess_privacy_risk"} <= tool_names
    assert risk_payload["id"] == "A-DL-01"
    assert assess_payload["system_name"] == "stdio round trip"
    assert "overall_score_pct" in assess_payload
    del mcp_client  # only used to trigger importorskip
