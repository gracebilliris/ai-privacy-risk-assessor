from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

from conftest import _free_port


@pytest.fixture()
def live_server_url(repo_root: Path) -> str:
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["CAPRA_PIA_API_BASE_URL"] = base_url

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "capra_pia.api:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        deadline = time.monotonic() + 15
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=5)
                pytest.fail(
                    "uvicorn exited before becoming healthy\n"
                    f"stdout:\n{stdout}\n"
                    f"stderr:\n{stderr}"
                )
            try:
                response = httpx.get(f"{base_url}/health", timeout=1)
                if response.status_code == 200 and response.json() == {"status": "ok"}:
                    break
            except Exception as exc:  # noqa: BLE001 - retry until the server is ready
                last_error = exc
                time.sleep(0.3)
        else:
            pytest.fail(f"uvicorn never became healthy: {last_error}")

        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_live_ui_submits_real_form_and_renders_report(repo_root: Path, live_server_url: str) -> None:
    payload = json.loads((repo_root / "examples" / "sample_ratings.json").read_text(encoding="utf-8"))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server_url}/ui/", wait_until="load")

        expect(page.locator("form.assessment-form")).to_be_visible(timeout=10_000)
        page.locator("#system_name").fill("Live UI browser test")
        for risk_id, rating in payload["ratings"].items():
            page.locator(f"#rating__{risk_id}").select_option(rating)

        page.get_by_role("button", name="Run assessment").click()

        expect(page.get_by_role("heading", name="Assessment Report")).to_be_visible(timeout=10_000)
        expect(page.locator(".error-panel")).to_have_count(0)
        expect(page.locator(".score-card").nth(0).locator(".score-value")).to_have_text("66.7%")
        expect(page.locator(".score-card").nth(1).locator(".score-value")).to_have_text("4")
        expect(page.locator(".score-card").nth(2).locator(".score-value")).to_have_text("0")

        flagged_section = page.locator(".panel").filter(
            has=page.get_by_role("heading", name="Flagged high-risk items")
        )
        expect(page.locator("body")).to_contain_text("Live UI browser test")
        for risk_id in ["A-DL-05", "A-ML-03", "A-IT-02", "B-GV-01"]:
            expect(flagged_section).to_contain_text(risk_id)

        browser.close()
