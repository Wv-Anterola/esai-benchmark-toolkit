# ESAI benchmark toolkit

Read-only scripts for the mapping work. The audit scripts run on a downloaded .xlsx export, not the
live sheet, and hash the file before and after so you can confirm they don't change it. The numbers
reflect whichever export you give them.

Needs Python with pandas and openpyxl:

    pip install pandas openpyxl

Drop the workbook export in this folder (or pass `--workbook`, or set `ESAI_WORKBOOK`), then:

    python workbook_health_check.py
    python coverage_gap_dashboard.py

`workbook_health_check.py` flags data problems worth fixing before pasting rows: the 32 colliding
benchmark IDs in the B332 to B363 range, `strength` values that aren't in the enums (like
`indirect`), the `empirical` vs `empirical study` split, dangling references, missing fields, and
coverage counts by subdomain.

`coverage_gap_dashboard.py` is the gap analysis. For each harm it takes the strongest edge and
buckets it (direct, strong, weak, or none), so you can see which risks have no direct benchmark or
only weak proxies. It writes the per-harm tables plus an HTML summary at
`outputs/gap_analysis/index.html`.

Both write to `./outputs/`. That folder and the .xlsx are gitignored.

## OpenReview benchmark extraction moved

The OpenReview collection pipeline that used to live here now sits under its work-package
folder: `../work-packages/systematic-benchmark-collection/` (collection + paper QC). See that
folder's README. The benchmark-to-risk "Mapping validation" work package is in
`../work-packages/mapping-validation/`.
