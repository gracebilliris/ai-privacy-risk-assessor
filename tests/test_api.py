from __future__ import annotations


def test_health_endpoint(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_risks_returns_full_taxonomy(client) -> None:
    response = client.get("/risks")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 40
    assert payload[0]["id"]
    assert payload[0]["source_paper"] in {"A", "B"}


def test_get_risk_returns_single_item_for_valid_id(client) -> None:
    response = client.get("/risks/A-DL-01")

    assert response.status_code == 200
    assert response.json()["id"] == "A-DL-01"


def test_get_risk_returns_404_for_unknown_id(client) -> None:
    response = client.get("/risks/NOPE-00")

    assert response.status_code == 404
    assert response.json()["detail"] == "Risk 'NOPE-00' not found"


def test_categories_endpoint_returns_category_counts(client) -> None:
    response = client.get("/categories")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 9
    assert sum(item["risk_count"] for item in payload) == 40
    assert {"category", "source_paper", "risk_count"} <= payload[0].keys()
    assert any(
        item == {
            "category": "Dataset-Level",
            "source_paper": "A",
            "risk_count": 5,
        }
        for item in payload
    )


def test_assess_endpoint_round_trip_returns_expected_shape(client) -> None:
    response = client.post(
        "/assess",
        json={
            "system_name": "API smoke test",
            "ratings": [
                {"risk_id": "A-ML-03", "rating": "present"},
                {"risk_id": "A-DL-01", "rating": "not_present"},
                {"risk_id": "B-GV-01", "rating": "present"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["system_name"] == "API smoke test"
    assert payload["overall_score_pct"] == 66.67
    assert len(payload["category_scores"]) == 9
    flagged_ids = {item["risk"]["id"] for item in payload["flagged_high_risk"]}
    assert {"A-ML-03", "B-GV-01"} <= flagged_ids
    assert "A-ML-03" not in payload["unrated_risks"]
    assert "A-DL-01" not in payload["unrated_risks"]
    assert "B-GV-01" not in payload["unrated_risks"]
    assert len(payload["unrated_risks"]) == 37
    assert len(payload["recommendations"]) == len(payload["flagged_high_risk"])
