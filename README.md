# ESAI mapping scripts

Two read-only scripts for checking the Harm-Benchmark-Legal mapping workbook. Both operate on a
downloaded `.xlsx` export rather than the live Google Sheet, and both hash the file before and after
running to confirm they never modify it. Treat the results as a snapshot of whichever export you
point them at.

## Requirements

Python 3.10 or later, with `pandas` and `openpyxl`:

```
pip install pandas openpyxl
```

## Usage

Place the workbook export in this folder, or pass its location with `--workbook` or the
`ESAI_WORKBOOK` environment variable, then run:

```
python workbook_health_check.py        # data-quality checks
python coverage_gap_dashboard.py        # coverage gap analysis
```

Output is written to `./outputs/`. The gap script also produces an HTML summary at
`outputs/gap_analysis/index.html`.

## What each script does

**workbook_health_check.py** reports data-quality issues that are worth resolving before adding or
pasting rows:

- duplicate or colliding `benchmark_id` values (currently 32, in the B332 to B363 range)
- `strength` values that are not in the `enums` tab (for example `indirect`)
- inconsistent `evidence_type` categories (`empirical` versus `empirical study`)
- dangling references and missing required fields
- coverage counts by domain and subdomain

**coverage_gap_dashboard.py** answers the coverage-gap question for the mapping. For each harm it
takes the strongest available benchmark edge and assigns a coverage tier (direct, strong proxy, weak
proxy, or none), then writes per-harm tables and a rollup by subdomain. This makes it straightforward
to see which risks have no direct benchmark and which have only weak proxies.

## Notes

Both scripts are standalone and have no dependencies beyond pandas and openpyxl. The workbook export
and the `outputs/` directory are git-ignored, so neither is committed.
