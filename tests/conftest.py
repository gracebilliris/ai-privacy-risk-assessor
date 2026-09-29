from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from capra_pia import api
from capra_pia.loader import load_risks


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def taxonomy(repo_root: Path):
    return load_risks(
        str(repo_root / "data" / "risks.yaml"),
        str(repo_root / "data" / "cross_references.yaml"),
    )


@pytest.fixture(scope="session")
def loaded_risks(taxonomy):
    risks, _ = taxonomy
    return risks


@pytest.fixture(scope="session")
def loaded_cross_references(taxonomy):
    _, cross_references = taxonomy
    return cross_references


@pytest.fixture()
def client() -> TestClient:
    return TestClient(api.app)
