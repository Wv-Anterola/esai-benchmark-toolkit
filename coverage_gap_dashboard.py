#!/usr/bin/env python3
"""
gap_analysis_dashboard.py  --  Systematic gap analysis of the benchmark->harm
mapping (addresses Yann's work package "Systematic gap analysis", 17-24 Jun 2026).

What it answers (per the work package):
  * Which risks (harms) have NO benchmark that measures them DIRECTLY?
  * Which risks have ONLY weak proxies?
  * Which risks are completely uncovered, and WHY (organisational? societal outcome?
    not-yet-collected?)
  * Roll up coverage by domain/subdomain for a dashboard.

Method (read-only):
  For every harm, take the BEST strength of any edge in `bench_measures_harm`:
    direct > strong-proxy > weak-proxy/contested/indirect > (none)
  and bucket the harm into a coverage tier. Then emit data CSVs + a self-contained
  HTML dashboard. Never writes to the source workbook (hashed before/after).

Usage:
  python scripts/gap_analysis_dashboard.py
Outputs (under outputs/gap_analysis/):
  harm_coverage_tiers.csv         -- all harms, tier + why_gap
  no_direct_coverage.csv          -- harms with proxies but no direct edge
  weak_proxy_only.csv             -- harms whose best edge is a weak proxy
  uncovered_harms.csv             -- harms with zero edges
  coverage_rollup_by_subdomain.csv
  index.html                      -- the dashboard
"""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

import pandas as pd

OUTDIR = Path("outputs/gap_analysis")


def find_workbook() -> Path | None:
    """First .xlsx in ./data (or ESAI_WORKBOOK env, or repo root)."""
    import os
    if os.environ.get("ESAI_WORKBOOK"):
        return Path(os.environ["ESAI_WORKBOOK"])
    for folder in ("data", "."):
        hits = sorted(Path(folder).glob("*.xlsx"))
        if hits:
            return hits[0]
    return None

STRENGTH_RANK = {"direct": 3, "strong-proxy": 2, "weak-proxy": 1, "contested": 1, "indirect": 1}
TIER_OF_RANK = {3: "DIRECT", 2: "STRONG-only", 1: "WEAK-only", 0: "NONE"}

# Canonical MIT subdomain names (from the MIT AI Risk Repository v4).
SUBDOMAIN_NAME = {
    "1.0": "Discrimination & Toxicity (general)",
    "1.1": "Unfair discrimination and misrepresentation",
    "1.2": "Exposure to toxic content",
    "1.3": "Unequal performance across groups",
    "2.0": "Privacy & Security (general)",
    "2.1": "Compromise of privacy",
    "2.2": "AI system security vulnerabilities and attacks",
    "3.0": "Misinformation (general)",
    "3.1": "False or misleading information",
    "3.2": "Pollution of information ecosystem",
    "4.0": "Malicious use (general)",
    "4.1": "Disinformation, surveillance, and influence at scale",
    "4.2": "Cyberattacks, weapon development or use, and mass harm",
    "4.3": "Fraud, scams, and targeted manipulation",
    "5.1": "Overreliance and unsafe use",
    "5.2": "Loss of human agency and autonomy",
    "6.0": "Socioeconomic & Environmental (general)",
    "6.1": "Power centralization and unfair distribution of benefits",
    "6.2": "Increased inequality and decline in employment quality",
    "6.3": "Economic and cultural devaluation of human effort",
    "6.4": "Competitive dynamics",
    "6.5": "Governance failure",
    "6.6": "Environmental harm",
    "7.0": "AI system safety, failures & limitations (general)",
    "7.1": "AI pursuing its own goals",
    "7.2": "AI possessing dangerous capabilities",
    "7.3": "Lack of capability or robustness",
    "7.4": "Lack of transparency or interpretability",
    "7.5": "AI welfare and rights",
    "7.6": "Multi-agent risks",
}

# Team ownership by subdomain (from the work-organization tab; inferred).
OWNER = {
    "1.1": "Emily", "1.2": "Emily", "1.3": "Emily",
    "2.1": "Pranav", "2.2": "Pranav",
    "3.0": "Kem", "3.1": "Kem", "3.2": "Kem",
    "4.0": "Kem", "4.1": "Kem", "4.2": "Kem", "4.3": "Kem",
    "5.1": "Ronan", "5.2": "Ronan",
    "6.1": "Wilber", "6.2": "Wilber",
    "6.3": "Yann", "6.4": "Yann", "6.5": "Yann", "6.6": "Yann",
    "7.1": "Pranav", "7.2": "Pranav",
    "7.3": "Yann", "7.4": "Yann", "7.5": "Yann", "7.6": "Yann",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def subdomain_code(harm_id: str) -> str:
    m = re.match(r"^(\d)\.(\d\d)", str(harm_id))
    return f"{m.group(1)}.{int(m.group(2))}" if m else "?"


def why_gap(row, uncovered_reason: dict) -> str:
    """Heuristic reason a harm lacks direct coverage. Grounded in uncovered_risks
    where available, else a domain-shape heuristic."""
    hid = row["harm_id"]
    if hid in uncovered_reason and str(uncovered_reason[hid]).strip() not in ("", "nan"):
        r = str(uncovered_reason[hid])
        if "not yet processed" in r.lower():
            return "not-yet-collected (subdomain not processed)"
        return f"flagged: {r[:60]}"
    sd = row["subdomain_code"]
    dom = sd[0]
    label = str(row["label"]).lower()
    if sd.endswith(".0"):
        return "general/parent leaf (often a descriptor, not a measurable harm)"
    if dom == "6":
        return "downstream societal/economic outcome (hard to measure directly)"
    if any(k in label for k in ("exploitation", "labour", "labor", "working condition")):
        return "human working-conditions harm (not a model property)"
    if any(k in label for k in ("inequality", "destabilis", "instability", "democracy", "rights")):
        return "broad societal/political outcome"
    if row["tier"] == "NONE":
        return "no edge yet, candidate for collection"
    return "proxy-measurable only (no direct operationalisation)"


def main() -> int:
    wb = find_workbook()
    if wb is None or not wb.exists():
        import sys
        print("ERROR: no workbook found. Put your ESAI .xlsx export in ./data/ "
              "(or set ESAI_WORKBOOK).", file=sys.stderr)
        return 2
    before = sha256(wb)
    xl = pd.ExcelFile(wb)
    harms = xl.parse("harms")
    edges = xl.parse("bench_measures_harm")
    uncovered = xl.parse("uncovered_risks")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    # best strength per harm
    best_rank = (edges.assign(r=edges["strength"].map(lambda s: STRENGTH_RANK.get(str(s), 0)))
                 .groupby("harm_id")["r"].max())
    n_by = lambda val: edges[edges["strength"] == val].groupby("harm_id").size()
    n_direct, n_strong = n_by("direct"), n_by("strong-proxy")
    n_edges = edges.groupby("harm_id").size()

    harms = harms.copy()
    harms["subdomain_code"] = harms["harm_id"].map(subdomain_code)
    harms["subdomain_name"] = harms["subdomain_code"].map(lambda c: SUBDOMAIN_NAME.get(c, "?"))
    harms["owner"] = harms["subdomain_code"].map(lambda c: OWNER.get(c, "UNOWNED/general"))
    harms["n_edges"] = harms["harm_id"].map(n_edges).fillna(0).astype(int)
    harms["n_direct"] = harms["harm_id"].map(n_direct).fillna(0).astype(int)
    harms["n_strong"] = harms["harm_id"].map(n_strong).fillna(0).astype(int)
    harms["best_rank"] = harms["harm_id"].map(best_rank).fillna(0).astype(int)
    harms["tier"] = harms["best_rank"].map(TIER_OF_RANK)

    uncovered_reason = dict(zip(uncovered["harm_id"], uncovered.get("why no benchmark", "")))
    harms["why_gap"] = harms.apply(lambda r: why_gap(r, uncovered_reason)
                                   if r["tier"] != "DIRECT" else "", axis=1)

    cols = ["harm_id", "label", "subdomain_code", "subdomain_name", "owner",
            "n_edges", "n_direct", "n_strong", "tier", "why_gap"]
    tiers = harms[cols].sort_values(["subdomain_code", "tier", "harm_id"])
    tiers.to_csv(OUTDIR / "harm_coverage_tiers.csv", index=False)

    no_direct = tiers[tiers["tier"].isin(["STRONG-only", "WEAK-only"])]
    no_direct.to_csv(OUTDIR / "no_direct_coverage.csv", index=False)
    tiers[tiers["tier"] == "WEAK-only"].to_csv(OUTDIR / "weak_proxy_only.csv", index=False)
    tiers[tiers["tier"] == "NONE"].to_csv(OUTDIR / "uncovered_harms.csv", index=False)

    # rollup
    roll = (harms.groupby(["subdomain_code", "subdomain_name", "owner"])
            .agg(n_harms=("harm_id", "size"),
                 direct=("tier", lambda s: (s == "DIRECT").sum()),
                 strong_only=("tier", lambda s: (s == "STRONG-only").sum()),
                 weak_only=("tier", lambda s: (s == "WEAK-only").sum()),
                 none=("tier", lambda s: (s == "NONE").sum()))
            .reset_index().sort_values("subdomain_code"))
    roll["pct_no_direct"] = ((roll["n_harms"] - roll["direct"]) / roll["n_harms"] * 100).round(0)
    roll.to_csv(OUTDIR / "coverage_rollup_by_subdomain.csv", index=False)

    write_dashboard(harms, roll, wb.name)

    after = sha256(wb)
    tc = harms["tier"].value_counts()
    print("=" * 60)
    print("SYSTEMATIC GAP ANALYSIS (local workbook finding)")
    print("=" * 60)
    print(f"workbook unmodified : {before == after}")
    print(f"total harms         : {len(harms)}")
    for t in ["DIRECT", "STRONG-only", "WEAK-only", "NONE"]:
        print(f"  {t:<12}: {int(tc.get(t,0)):>4}  ({tc.get(t,0)/len(harms)*100:.0f}%)")
    no_direct_total = len(harms) - int(tc.get("DIRECT", 0))
    print(f"NO DIRECT MEASURE   : {no_direct_total} harms ({no_direct_total/len(harms)*100:.0f}%)")
    print(f"  of which uncovered: {int(tc.get('NONE',0))}")
    print(f"  weak-proxy only   : {int(tc.get('WEAK-only',0))}")
    print(f"wrote dashboard + 5 CSVs under {OUTDIR}/")
    return 0


def write_dashboard(harms: pd.DataFrame, roll: pd.DataFrame, wb_name: str) -> None:
    tc = harms["tier"].value_counts()
    total = len(harms)
    COLORS = {"DIRECT": "#2e7d32", "STRONG-only": "#9e9d24",
              "WEAK-only": "#ef6c00", "NONE": "#c62828"}

    def bar(r):
        seg = ""
        for t in ["DIRECT", "STRONG-only", "WEAK-only", "NONE"]:
            v = int(r[{"DIRECT": "direct", "STRONG-only": "strong_only",
                       "WEAK-only": "weak_only", "NONE": "none"}[t]])
            if v:
                pct = v / r["n_harms"] * 100
                seg += (f'<span title="{t}: {v}" style="display:inline-block;width:{pct:.1f}%;'
                        f'background:{COLORS[t]};height:14px"></span>')
        return seg

    rows = ""
    for _, r in roll.iterrows():
        rows += (f"<tr><td>{html.escape(r['subdomain_code'])}</td>"
                 f"<td>{html.escape(str(r['subdomain_name']))}</td>"
                 f"<td>{html.escape(str(r['owner']))}</td>"
                 f"<td style='text-align:right'>{int(r['n_harms'])}</td>"
                 f"<td style='text-align:right'>{int(r['pct_no_direct'])}%</td>"
                 f"<td style='width:240px'>{bar(r)}</td></tr>")

    cards = ""
    for t in ["DIRECT", "STRONG-only", "WEAK-only", "NONE"]:
        v = int(tc.get(t, 0))
        cards += (f"<div class='card' style='border-top:4px solid {COLORS[t]}'>"
                  f"<div class='n'>{v}</div><div class='l'>{t}<br><small>{v/total*100:.0f}%</small></div></div>")
    no_direct_total = total - int(tc.get("DIRECT", 0))

    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>ESAI Gap Analysis</title><style>
body{{font:14px/1.5 system-ui,Arial;margin:24px;color:#222;max-width:1000px}}
h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px}}
.cards{{display:flex;gap:12px;margin:12px 0}}
.card{{flex:1;background:#fafafa;border:1px solid #ddd;border-radius:6px;padding:12px;text-align:center}}
.card .n{{font-size:26px;font-weight:700}} .card .l{{color:#555}}
.big{{font-size:30px;font-weight:700;color:#c62828}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border-bottom:1px solid #eee;padding:5px 7px;text-align:left}}
th{{background:#f3f3f3}} .note{{color:#666;font-size:12px}}
.legend span{{display:inline-block;width:12px;height:12px;margin:0 4px -1px 10px;border-radius:2px}}
</style></head><body>
<h1>ESAI Systematic Gap Analysis</h1>
<p class="note">Addresses Yann's work package <b>"Systematic gap analysis"</b> (17-24 Jun 2026).
<b>Local workbook finding</b> from <code>{html.escape(wb_name)}</code>, not the live sheet.
Coverage tier = best strength of any benchmark-to-harm edge.</p>

<div class="cards">{cards}</div>
<p><span class="big">{no_direct_total}</span> of {total} harms
({no_direct_total/total*100:.0f}%) have <b>no benchmark that measures them directly</b>
&mdash; the headline gap for collection &amp; the construct-validity sprint.</p>

<p class="legend"><b>Legend:</b>
<span style="background:{COLORS['DIRECT']}"></span>direct
<span style="background:{COLORS['STRONG-only']}"></span>strong-only
<span style="background:{COLORS['WEAK-only']}"></span>weak-only
<span style="background:{COLORS['NONE']}"></span>uncovered</p>

<h2>Coverage by subdomain</h2>
<table><tr><th>Code</th><th>Subdomain</th><th>Owner</th><th>#harms</th>
<th>% no-direct</th><th>tier mix</th></tr>{rows}</table>

<h2>How to use this</h2>
<ul>
<li><b>Uncovered (red)</b> &rarr; collection targets. See <code>uncovered_harms.csv</code>.</li>
<li><b>Weak-only (orange)</b> &rarr; either better benchmarks exist or the risk is intrinsically
hard to measure. See <code>weak_proxy_only.csv</code> + the <code>why_gap</code> column.</li>
<li><b>No-direct (orange+yellow)</b> &rarr; candidates for the construct-validity work package.
See <code>no_direct_coverage.csv</code>.</li>
</ul>
<p class="note">Regenerate: <code>python scripts/gap_analysis_dashboard.py</code>.
Source workbook is opened read-only and hash-checked; never modified.</p>
</body></html>"""
    (OUTDIR / "index.html").write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
