from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "capra_pia.cli", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_list_risks_prints_all_40_rows(repo_root: Path) -> None:
    result = _run_cli("list-risks", cwd=repo_root)

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 40

    first_columns = lines[0].split("\t")
    assert first_columns[0] == "A-DL-01"
    assert first_columns[3] == "A"


def test_assess_produces_valid_json_and_summary(tmp_path: Path, repo_root: Path) -> None:
    ratings_path = tmp_path / "ratings.json"
    ratings_path.write_text(
        json.dumps(
            {
                "system_name": "CLI subprocess test",
                "ratings": {
                    "A-ML-03": "present",
                    "A-DL-01": "not_present",
                    "B-GV-01": "present",
                    "A-IT-02": "not_applicable",
                },
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli("assess", str(ratings_path), cwd=repo_root)

    assert result.returncode == 0, result.stderr
    assert "Summary" in result.stdout
    assert "System: CLI subprocess test" in result.stdout
    assert "Unrated risks: 36" in result.stdout

    json_blob = result.stdout.split("\nSummary", 1)[0]
    payload = json.loads(json_blob)
    assert payload["system_name"] == "CLI subprocess test"
    assert payload["overall_score_pct"] == 66.67
    assert len(payload["unrated_risks"]) == 36
    flagged_ids = {item["risk"]["id"] for item in payload["flagged_high_risk"]}
    assert flagged_ids >= {"A-ML-03", "B-GV-01"}


def test_assess_rejects_malformed_ratings_file(tmp_path: Path, repo_root: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("[1, 2, 3]", encoding="utf-8")

    result = _run_cli("assess", str(bad_path), cwd=repo_root)

    assert result.returncode != 0
    assert "Ratings JSON must be an object" in result.stderr


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_serve_starts_a_working_http_server(repo_root: Path) -> None:
    httpx = pytest.importorskip("httpx")
    port = _free_port()

    process = subprocess.Popen(
        [sys.executable, "-m", "capra_pia.cli", "serve", "--port", str(port)],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1)
                if response.status_code == 200:
                    assert response.json() == {"status": "ok"}
                    break
            except Exception as exc:  # noqa: BLE001 - retry until the server is up
                last_error = exc
                time.sleep(0.3)
        else:
            pytest.fail(f"capra-pia serve never became healthy: {last_error}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
