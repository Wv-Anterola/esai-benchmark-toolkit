# ESAI Benchmark Toolkit

Shared, reusable tooling for the EuroSafeAI / Jinesis **Harm-Benchmark-Legal Mapping** project:
the workbook audit, the coverage-gap dashboard, the shared prompts, the row templates, and the
coding cheat-sheet. Clone it, drop in your workbook export, and everything runs.

> All tools are **read-only** on the workbook and hash-check it to prove they never modify it.
> Findings are from your **local export**, not the live Google Sheet.

## Quick start

```bash
git clone <repo-url>
cd esai-benchmark-toolkit
bash setup.sh                 # makes a venv + installs pandas/openpyxl
# Windows (PowerShell): python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt

# put your workbook export in ./data/  (File -> Download -> .xlsx from the live sheet)
python tools/workbook_health_check.py        # integrity + coverage audit  -> outputs/*.csv
python tools/coverage_gap_dashboard.py        # gap analysis -> outputs/gap_analysis/index.html
```

No `git`? Just download the ZIP, run `pip install -r requirements.txt`, and the same two commands.

## What's inside

| Path | What it is |
|---|---|
| `tools/workbook_health_check.py` | Integrity + coverage audit: duplicate/colliding IDs, dangling refs, missing fields, enum problems, coverage by subdomain. Writes `outputs/id_integrity_issues.csv` + `outputs/coverage_by_domain.csv`. |
| `tools/coverage_gap_dashboard.py` | Per-harm coverage tiers (direct / strong-proxy / weak-proxy / none) → an HTML dashboard + CSV data layers under `outputs/gap_analysis/`. Answers "which risks have no direct benchmark / only weak proxies." |
| `prompts/validate-benchmark-harm-mapping.md` | Reusable prompt to validate (or correct) a benchmark→harm mapping against the coding rubric. |
| `guides/coding-conventions-cheatsheet.md` | One-page summary of the ID format, what to fill vs. leave blank, the enums, and the strength rubric. |
| `guides/adding-rows-and-qc-checklist.md` | How to produce rows + a pre-paste QC checklist. |
| `templates/` | Empty CSVs whose headers exactly match the live sheet tabs — fill and paste. |
| `examples/` | Worked example rows (web-verified agentic benchmarks → MIT 6.2). |
| `data/` | Drop your `.xlsx` export here (git-ignored). |

## Typical workflow
1. Download the latest workbook export → `data/`.
2. `python tools/workbook_health_check.py` to see data-quality issues before you add rows.
3. Use a `templates/` file + `guides/coding-conventions-cheatsheet.md` to add rows.
4. Run the QC checklist (`guides/adding-rows-and-qc-checklist.md`) before pasting into the live sheet.
5. `python tools/coverage_gap_dashboard.py` to see where the gaps are.

## Conventions in one line
`benchmark_id = BX.YY.ZZ` · fill only the input columns (the `Bench:`/`Harm:` columns
auto-populate) · `strength ∈ {direct, strong-proxy, weak-proxy, contested}` · default
`basis = face-validity-only` · one benchmark can map to many harms · flag unmeasurable leaves
rather than forcing a weak mapping.

## Publishing this to GitHub
```bash
# from inside esai-benchmark-toolkit/
git init && git add . && git commit -m "ESAI benchmark toolkit: audit, gap dashboard, prompts, templates"
git branch -M main
git remote add origin git@github.com:<org-or-user>/esai-benchmark-toolkit.git
git push -u origin main
```
The workbook and `outputs/` are git-ignored, so nothing sensitive is committed.

## Contributing
Tools are plain Python + pandas, no framework. Add a new tool under `tools/`, a new prompt under
`prompts/`, and keep file names human-readable (kebab-case).
