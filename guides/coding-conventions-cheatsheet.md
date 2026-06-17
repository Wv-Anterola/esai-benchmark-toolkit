# Coding conventions cheat-sheet

A one-page summary of Yann's coding guide, so rows go in consistently. (The full guide lives in the
project Google Doc , this is just the quick reference.)

## IDs
- **`benchmark_id` = `BX.YY.ZZ`** , `X` = paper/suite, `YY` = task (start `01`), `ZZ` = metric
 (start `01`). Every paper has at least one `BX.01.01` row with `task` + `metric` filled.
 Add a row and bump `YY` for a new task, `ZZ` for a new metric.
- **`harm_id` = `D.SS.LL`** , domain.subdomain.leaf (e.g. `6.02.01`). Add to the end of the
 subdomain; only add `harm_id` + `ev_id` if the harm doesn't exist yet.

## benchmarks tab , fill these
`benchmark_id`, `quick ref` (FirstAuthorSurname+Year, e.g. `Jin2026`; clash -> `Jin2026a/b`),
`title`, `task`, `metric`, `communicated_metric`, `version` = 1, `notes` (your reasoning),
`evidence_type`.
**Leave blank for now:** `modality`, `interaction horizon`, `aggregation scale` (Tae owns these).

## bench_measures_harm tab , fill these
`benchmark_id`, `harm_id`, `strength`, `basis`, `confidence`, `annotator`, `version` = 1, `notes`.
**Leave blank (auto-populated):** `edge_id`, `ev_id`, `Bench: Title`, `Harm: Category`,
`Harm: Subcategory`, `Harm: Domain`, `Harm: Subdomain`.

## Controlled vocabulary (must match the `enums` tab)
- **strength:** `direct` | `strong-proxy` | `weak-proxy` | `contested` (NOT `indirect`)
- **basis:** `validated-against-downstream` | `face-validity-only` | `known-non-correlation`
- **coverage (legal):** `explicit` | `interpretive` | `contested`

## Strength rubric (diagnostics)
- **direct** , the score *is* an instance of the harm. *Can you call a high score "the model did
 the harmful thing" with no added assumptions?*
- **strong-proxy** , a near-necessary precursor/component; short, well-established chain.
- **weak-proxy** , correlated across inferential distance / confounds / repurposed benchmark.
- **none** , it doesn't measure the harm.
- Default `basis` = `face-validity-only` unless validated against downstream outcomes.
- For socioeconomic / downstream harms (6.x labour, inequality, power): default to proxy, not direct.

## Multiple harms
One benchmark can map to many harms , add one edge row per (benchmark, harm). Flag broad or
unmeasurable taxonomy leaves in `uncovered_risks` instead of forcing a weak mapping.
