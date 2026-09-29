# Consolidation decisions — audit log

## 1. B-UC-06 merged into B-UC-03 (Paper B duplicate row)

Source Table (Paper B, *Category: User-Centric Privacy Considerations*)
contains two near-identical rows:

| Original ID | Name | Count | % |
|---|---|---|---|
| B-UC-03 (kept) | User Consent & Control Mechanisms | 47 | 6.58% |
| B-UC-06 (removed) | User Consent & Control Risks | 38 | 5.32% |

Decision (2026-09-29, user instruction): treat as a duplication artefact in
the source paper's table and merge into a single item, `B-UC-03`. Paper B's
working risk count for the tool therefore drops from 22 to **21**; combined
total taxonomy size is **40** (19 from Paper A + 21 from Paper B), not 41.

No statistics were averaged or combined — `B-UC-03`'s original count/%
(47 / 6.58%) is retained as-is; `B-UC-06`'s row is dropped rather than merged
numerically, since the two counts likely reflect the same underlying
literature mentions counted twice rather than two additive risks.

⚠️ This is an editorial judgement call by the tool team, not a correction
issued by the paper's authors. Recommend a quick sanity check with
Asif/Madhushi before treating `risks.yaml` as final/citable.

## 2. Cross-references between Paper A and Paper B risks

See `cross_references.yaml`. Paper A (component-oriented: dataset/model/
infrastructure/insider) and Paper B (lifecycle/governance-oriented:
governance/assessment/controls/user/monitoring, AI+quantum) are **not**
simple subsets of each other — they classify risks along different axes.
Rather than merging them into one flat list, each Paper A risk that is
explicitly named (verbatim or near-verbatim keyword) inside a Paper B risk's
own published definition is recorded as a directional cross-reference:
`A risk → instance/example within B risk`.

This mapping is analytical (built by matching explicit keyword overlap in
the two papers' own definition text), not a mapping stated by the authors
themselves — it should inform, not replace, judgement in the scoring engine,
and is worth confirming with the authors before being treated as
authoritative.
