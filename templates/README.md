# templates/

Empty CSVs whose headers **exactly match** the live ESAI sheet tabs (column order + spelling,
including the trailing space in `Harm: Category `). Copy a template, add your rows, then paste
under the matching tab.

| Template | Pastes into tab |
|---|---|
| `benchmarks-row-template.csv` | `benchmarks` |
| `bench-measures-harm-row-template.csv` | `bench_measures_harm` |
| `provision-addresses-harm-row-template.csv` | `provision_addresses_harm` |

**What to fill (per the coding guide):**
- **benchmarks:** `benchmark_id` (`BX.YY.ZZ`), `quick ref` (FirstAuthorSurname+Year, e.g. `Jin2026`),
 `title`, `task`, `metric`, `communicated_metric`, `version`=1, `notes`, `evidence_type`.
 Leave `modality` / `interaction horizon` / `aggregation scale` **blank** (Tae's job for now).
- **bench_measures_harm:** fill `benchmark_id`, `harm_id`, `strength`, `basis`, `confidence`,
 `annotator`, `version`=1, `notes`. Leave `edge_id`, `ev_id`, `Bench: Title`, `Harm: Category`,
 `Harm: Subcategory`, `Harm: Domain`, `Harm: Subdomain` **blank** , they auto-populate from
 `benchmark_id` / `harm_id`.
- **provision_addresses_harm:** only if clearly supported by the coding guide (it is a layered,
 scenario-based argument, not one row per provision).

See `guides/coding-conventions-cheatsheet.md` and `guides/adding-rows-and-qc-checklist.md`.
