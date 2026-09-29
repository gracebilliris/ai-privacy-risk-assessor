from __future__ import annotations

from pathlib import Path
from typing import Union

import yaml

from capra_pia.models import CrossReference, Risk


def _read_yaml(path: Union[str, Path]) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level in {path}")
    return data


def load_risks(
    risks_path: str, cross_refs_path: str
) -> tuple[list[Risk], list[CrossReference]]:
    """Parse data/risks.yaml and data/cross_references.yaml into typed models."""

    risks_data = _read_yaml(risks_path)
    cross_refs_data = _read_yaml(cross_refs_path)

    risks: list[Risk] = []
    for source_key, source_paper in (("source_a", "A"), ("source_b", "B")):
        source_block = risks_data.get(source_key)
        if not isinstance(source_block, dict):
            raise ValueError(f"Missing or invalid '{source_key}' block in {risks_path}")

        citation = source_block.get("citation")
        if not isinstance(citation, str):
            raise ValueError(f"Missing citation for {source_key} in {risks_path}")

        categories = source_block.get("categories")
        if not isinstance(categories, list):
            raise ValueError(f"Missing categories for {source_key} in {risks_path}")

        for category_entry in categories:
            if not isinstance(category_entry, dict):
                raise ValueError(f"Invalid category entry in {risks_path}")

            category_name = category_entry.get("name")
            if not isinstance(category_name, str):
                raise ValueError(f"Category missing name in {risks_path}")

            category_risks = category_entry.get("risks")
            if not isinstance(category_risks, list):
                raise ValueError(f"Category '{category_name}' missing risks in {risks_path}")

            for risk_entry in category_risks:
                if not isinstance(risk_entry, dict):
                    raise ValueError(f"Invalid risk entry under category '{category_name}'")

                risks.append(
                    Risk(
                        id=risk_entry["id"],
                        name=risk_entry["name"],
                        category=category_name,
                        source_paper=source_paper,
                        source_citation=citation,
                        frequency_count=risk_entry["frequency_count"],
                        frequency_pct=risk_entry["frequency_pct"],
                        definition=risk_entry["definition"],
                        category_tag=risk_entry.get("category_tag"),
                        note=risk_entry.get("note"),
                    )
                )

    cross_ref_entries = cross_refs_data.get("cross_references")
    if not isinstance(cross_ref_entries, list):
        raise ValueError(f"Missing cross_references list in {cross_refs_path}")

    cross_refs = [CrossReference.model_validate(entry) for entry in cross_ref_entries]
    return risks, cross_refs
