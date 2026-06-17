# Row-Production Template + QC + Source-Grounding Checklist

**Author:** Wilber · **Date:** 2026-06-16 · For: any contributor adding rows to the ESAI map.
Basis: local workbook inspection (`ESAI Harm-Bench-Legal Map (1).xlsx`) + the legal coding guide.
Goal: defensible, source-grounded rows that paste cleanly after owner review. **Never edit the
live sheet / source workbooks — produce generated CSVs, then hand to the owner.**

## A. Target sheet columns (match exactly)

**`benchmarks`** (13): `benchmark_id, quick ref, title, description, task, metric,
communicated_metric, modality, interaction horizon, aggregation scale, version, notes,
evidence_type`.

**`bench_measures_harm`** (15): `edge_id, benchmark_id, harm_id, ev_id, Bench: Title,
Harm: Category, Harm: Subcategory, Harm: Domain, Harm: Subdomain, strength, basis, confidence,
annotator, version, notes`.
> The `Bench:` / `Harm:` columns **auto-populate** in the live sheet (the guide says they are
> "automagically pulled in"). You only need a valid `benchmark_id` + `harm_id` + the annotation
> fields. `edge_id` is assigned in-sheet — leave a draft placeholder.

**`provision_addresses_harm`** (9): only create if the coding guide clearly supports the link;
otherwise hold (see `DO_NOT_PASTE_LEGAL_ROWS_YET.md`).

## B. Required status columns on every generated row (this project's convention)
`owner_status` · `track` (Track A / Track B / Both) · `verification_status`
(`web_verified` / `locally_verified` / `source_in_workbook` / `needs_external_verification`) ·
`source_status` (same vocab; is the benchmark source itself grounded — e.g. confirmed via
arXiv/venue?) · `paste_status`
(`owner_review_needed` / `DRAFT — official benchmark_id must be assigned before pasting`) ·
`owner_collision_risk` (`none` / `ID-collision` / `lane-overlap:<owner>`) · `notes` (the
strength/basis rationale).

## C. Strength rubric (from the coding guide — do not deviate)
- `direct` — the score **is** an instance of the harm. Diagnostic: can you call a high score
  "the model did the harmful thing" with **no added assumptions**? If not → not direct.
- `strong-proxy` — measures a near-necessary precursor/component; short, well-established chain.
- `weak-proxy` — correlated across substantial inferential distance / confounds / repurposed
  general benchmark.
- `contested` — plausible but debatable.
- `basis` defaults to `face-validity-only` unless the source validates against downstream
  outcomes (`validated-against-downstream`).
- For socioeconomic / downstream harms (6.x labour, inequality, power): default to weak/strong
  proxy — almost never `direct`.

## D. Source-grounding checklist (before a benchmark row is allowed)
- [ ] Source is a real **benchmark / eval suite / dataset / model-card eval / paper with concrete
      eval tasks+metrics** — NOT a risk-framework or policy paper.
- [ ] If present in the workbook → reuse its `benchmark_id`; set `source_status=source_in_workbook`.
- [ ] If not local and not web-verified → `needs_external_verification` + precise search terms;
      do **not** invent task/metric/year.
- [ ] Benchmark is not a colliding ID (`B332–B363`); if it is, flag `owner_collision_risk=ID-collision`.

## E. Pre-paste QC checklist (run before handing rows to an owner)
- [ ] CSV parses (pandas), headers present.
- [ ] every `harm_id` exists in `harms` (no dangling/new harm_ids).
- [ ] `strength` ∈ {direct, strong-proxy, weak-proxy, contested}; `basis` ∈
      {validated-against-downstream, face-validity-only, known-non-correlation}; no `indirect`.
- [ ] no `direct` unless the score literally instances the harm (justify in notes).
- [ ] each row has all status columns (§B) filled.
- [ ] draft rows separated from coordinate-only rows; owner tagged.
- [ ] broad/unbenchmarkable harms routed to a HOLD file, not forced into mappings.
- [ ] no source workbook modified (hash check via `scripts/audit_esai_workbook.py`).

## F. Minimal copy-paste row stubs

`bench_measures_harm` draft (CSV header):
```
draft_benchmark_id,benchmark_name,harm_id,harm_name,strength,basis,confidence,owner_status,track,verification_status,source_status,paste_status,owner_collision_risk,notes
```
`benchmarks` draft (CSV header):
```
draft_benchmark_id,title,quick_ref,description,task,metric,modality,interaction_horizon,evidence_type,owner_status,track,verification_status,source_status,paste_status,source_or_search_terms,notes
```
