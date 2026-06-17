#!/usr/bin/env python3
"""
audit_esai_workbook.py  --  read-only integrity & coverage audit for the
ESAI Harm-Bench-Legal Map workbook.

Purpose
-------
Reusable, idempotent audit that the whole team can re-run. It NEVER writes to
the source .xlsx files (they are opened read-only and hashed before/after to
prove it). It emits machine-readable CSVs under ./outputs and prints a summary.

Checks
------
  * ID integrity            -- dangling edge refs, ID format, COLLIDING benchmark_ids
  * Required fields          -- missing strength/basis/confidence/notes on edges
  * Enum validity            -- edge/benchmark values vs the `enums` sheet (+ evidence_type drift)
  * Coverage                 -- edges per domain/subdomain, distinct benchmarks, strength/basis mix
  * Strength inflation       -- edges marked `direct` while basis is `face-validity-only`
  * BX.YY.ZZ convention      -- whether the task/metric decomposition was applied

Usage
-----
  python scripts/audit_esai_workbook.py
  python scripts/audit_esai_workbook.py --workbook "ESAI Harm-Bench-Legal Map (1).xlsx"

Outputs
-------
  outputs/coverage_by_domain.csv
  outputs/id_integrity_issues.csv

Source-of-truth caveat: this audits the *local* workbook copy, not the live
Google Sheet. Phrase findings as "local workbook finding".
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

ID_RE = re.compile(r"^B\d+\.\d+\.\d+$")
REQUIRED_EDGE_FIELDS = ["strength", "basis", "confidence", "notes"]


def find_workbook(explicit: str | None = None) -> Path | None:
    """Resolve the workbook: --workbook arg, else ESAI_WORKBOOK env, else the
    first .xlsx in ./data, else the first .xlsx in the repo root."""
    import os
    if explicit:
        return Path(explicit)
    if os.environ.get("ESAI_WORKBOOK"):
        return Path(os.environ["ESAI_WORKBOOK"])
    for folder in ("data", "."):
        hits = sorted(Path(folder).glob("*.xlsx"))
        if hits:
            return hits[0]
    return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load(workbook: Path) -> dict[str, pd.DataFrame]:
    """Open the workbook read-only and return the sheets we audit."""
    xl = pd.ExcelFile(workbook)  # read-only; pandas never writes back
    want = ["harms", "benchmarks", "bench_measures_harm", "enums",
            "provision_addresses_harm", "uncovered_risks"]
    return {s: xl.parse(s) for s in want if s in xl.sheet_names}


def check_id_integrity(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    bm = sheets["benchmarks"]
    h = sheets["harms"]
    edges = sheets["bench_measures_harm"]

    valid_bench = set(bm["benchmark_id"])
    valid_harm = set(h["harm_id"])

    # Colliding benchmark_ids: same id, different benchmarks
    dup_mask = bm["benchmark_id"].duplicated(keep=False)
    for bid, grp in bm[dup_mask].groupby("benchmark_id"):
        titles = " || ".join(str(t)[:70] for t in grp["title"].tolist())
        rows.append(dict(issue_type="colliding_benchmark_id", entity=bid,
                         detail=f"{len(grp)} benchmarks share this id: {titles}",
                         severity="high"))

    # Dangling edge references
    for bid in sorted(set(edges["benchmark_id"]) - valid_bench):
        rows.append(dict(issue_type="dangling_benchmark_id", entity=bid,
                         detail="edge references benchmark_id absent from benchmarks",
                         severity="high"))
    for hid in sorted(set(edges["harm_id"]) - valid_harm):
        rows.append(dict(issue_type="dangling_harm_id", entity=hid,
                         detail="edge references harm_id absent from harms",
                         severity="high"))

    # ID format
    for bid in bm["benchmark_id"].dropna():
        if not ID_RE.match(str(bid)):
            rows.append(dict(issue_type="bad_id_format", entity=bid,
                             detail="benchmark_id does not match B<num>.<task>.<metric>",
                             severity="medium"))

    # BX.YY.ZZ convention: are task/metric segments ever > 01?
    seg = bm["benchmark_id"].dropna().astype(str).str.extract(r"^B\d+\.(\d+)\.(\d+)$")
    flat = ((seg[0] == "01") & (seg[1] == "01")).sum()
    total = seg[0].notna().sum()
    if total and flat == total:
        rows.append(dict(issue_type="flat_bx_yy_zz", entity="ALL",
                         detail=f"all {total} ids are B*.01.01 -- task/metric "
                                "decomposition (BX.YY.ZZ) was never applied",
                         severity="medium"))
    return pd.DataFrame(rows, columns=["issue_type", "entity", "detail", "severity"])


def check_required_fields(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    edges = sheets["bench_measures_harm"]
    rows = []
    for f in REQUIRED_EDGE_FIELDS:
        n = edges[f].isna().sum() if f in edges.columns else len(edges)
        rows.append(dict(field=f, missing=int(n), total=len(edges)))
    return pd.DataFrame(rows)


def check_enums(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    enums = sheets["enums"]
    edges = sheets["bench_measures_harm"]
    allowed = {c: set(str(v) for v in enums[c].dropna()) for c in enums.columns}
    rows = []
    for col in ["strength", "basis"]:
        bad = set(str(v) for v in edges[col].dropna()) - allowed.get(col, set())
        for v in sorted(bad):
            rows.append(dict(sheet="bench_measures_harm", column=col,
                             bad_value=v, note="not in enums"))
    # evidence_type drift (benchmarks sheet is not enum-controlled but should be)
    et = sheets["benchmarks"]["evidence_type"].dropna().astype(str)
    vc = et.value_counts().to_dict()
    if "empirical" in vc and "empirical study" in vc:
        rows.append(dict(sheet="benchmarks", column="evidence_type",
                         bad_value="empirical / empirical study",
                         note=f"near-duplicate categories ({vc.get('empirical')} vs "
                              f"{vc.get('empirical study')}) -- normalize"))
    return pd.DataFrame(rows, columns=["sheet", "column", "bad_value", "note"])


def coverage_by_domain(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    edges = sheets["bench_measures_harm"].copy()
    edges["Harm: Domain"] = edges["Harm: Domain"].astype(str)
    edges["Harm: Subdomain"] = edges["Harm: Subdomain"].astype(str)
    rows = []
    for (dom, sub), grp in edges.groupby(["Harm: Domain", "Harm: Subdomain"]):
        sm = grp["strength"].value_counts().to_dict()
        bm = grp["basis"].value_counts().to_dict()
        rows.append(dict(
            domain=dom, subdomain=sub, n_edges=len(grp),
            distinct_benchmarks=grp["benchmark_id"].nunique(),
            distinct_harms=grp["harm_id"].nunique(),
            n_direct=sm.get("direct", 0), n_strong=sm.get("strong-proxy", 0),
            n_weak=sm.get("weak-proxy", 0), n_contested=sm.get("contested", 0),
            n_face_validity=bm.get("face-validity-only", 0),
            n_validated=bm.get("validated-against-downstream", 0),
            n_direct_and_face_validity=len(grp[(grp["strength"] == "direct") &
                                               (grp["basis"] == "face-validity-only")]),
        ))
    out = pd.DataFrame(rows).sort_values(["domain", "subdomain"]).reset_index(drop=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workbook", default=None,
                    help="path to the workbook (default: first .xlsx in ./data)")
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()

    wb = find_workbook(args.workbook)
    if wb is None or not wb.exists():
        print("ERROR: no workbook found. Put your ESAI .xlsx export in ./data/ "
              "or pass --workbook PATH.", file=sys.stderr)
        return 2
    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    before = sha256(wb)
    sheets = load(wb)

    integrity = check_id_integrity(sheets)
    fields = check_required_fields(sheets)
    enum_issues = check_enums(sheets)
    coverage = coverage_by_domain(sheets)

    integrity.to_csv(outdir / "id_integrity_issues.csv", index=False)
    coverage.to_csv(outdir / "coverage_by_domain.csv", index=False)

    after = sha256(wb)

    print("=" * 64)
    print("ESAI WORKBOOK AUDIT  (local workbook finding -- not the live sheet)")
    print("=" * 64)
    print(f"workbook            : {wb.name}")
    print(f"sha256 before       : {before}")
    print(f"sha256 after        : {after}")
    print(f"workbook unmodified : {before == after}")
    print("-" * 64)
    print(f"colliding bench ids : {(integrity['issue_type'] == 'colliding_benchmark_id').sum()}")
    print(f"dangling refs       : {integrity['issue_type'].str.startswith('dangling').sum()}")
    print(f"bad id format       : {(integrity['issue_type'] == 'bad_id_format').sum()}")
    print(f"flat BX.YY.ZZ       : {(integrity['issue_type'] == 'flat_bx_yy_zz').sum()} (1 = convention never applied)")
    print("-" * 64)
    print("missing required edge fields:")
    for _, r in fields.iterrows():
        print(f"   {r['field']:<11}: {r['missing']}/{r['total']}")
    print("-" * 64)
    print(f"enum issues         : {len(enum_issues)}")
    for _, r in enum_issues.iterrows():
        print(f"   {r['sheet']}.{r['column']}: {r['bad_value']} -- {r['note']}")
    print("-" * 64)
    d6 = coverage[coverage["subdomain"].str.startswith("6")]
    print("domain-6 coverage (edges | distinct benchmarks | direct+face-validity):")
    for _, r in d6.iterrows():
        print(f"   {r['subdomain'][:48]:<48} {r['n_edges']:>4} | "
              f"{r['distinct_benchmarks']:>3} | {r['n_direct_and_face_validity']:>3}")
    print("-" * 64)
    print(f"wrote: {outdir / 'id_integrity_issues.csv'}")
    print(f"wrote: {outdir / 'coverage_by_domain.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
