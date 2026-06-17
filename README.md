# Two scripts for the ESAI map

Both are read-only on the workbook (they hash it before and after to prove they don't change it),
and both work off a downloaded .xlsx export, not the live sheet, so treat the numbers as a snapshot.

## Run them

You need Python with pandas and openpyxl:

```
pip install pandas openpyxl
```

Put the workbook export (.xlsx) in this folder, or point at it with `--workbook` or the
`ESAI_WORKBOOK` env var, then:

```
python workbook_health_check.py        # data issues: colliding IDs, bad enums, coverage counts
python coverage_gap_dashboard.py        # which harms have no/weak benchmark coverage
```

Results land in `./outputs/` (the gap dashboard also writes `outputs/gap_analysis/index.html`).

## What they're for

- **workbook_health_check.py** catches the data problems before you paste rows: the 32 colliding
  benchmark IDs (B332 to B363), the `strength = indirect` values that aren't in the enums, the
  `empirical` vs `empirical study` split, dangling references, missing fields, and coverage by
  subdomain.
- **coverage_gap_dashboard.py** is the gap analysis for Yann's work package: for every harm it
  takes the best strength of any edge and buckets it (direct / strong / weak / none), so you can
  see which risks have no direct benchmark or only weak proxies.

That's it. No setup script, no framework, just two files you can run or hand to whoever wants them.
