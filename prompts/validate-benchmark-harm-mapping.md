# Mapping Validation Prompt — `bench_measures_harm` edges

A reusable prompt to validate (or correct) a benchmark→harm edge before it is trusted. It is
grounded in the **project's own coding rubric** (legal framework md, "Benchmark measures → Harm",
lines 288-301) and the `enums` controlled vocabulary, so its verdicts are consistent with how the
team already codes. Built to catch the two patterns the audit found: **risk-framework papers
treated as benchmarks** and **`direct` strength on `face-validity-only` basis** (strength
inflation).

> Use during the validity sprint, or as a second-pass QC on agent-generated edges. It is a
> *review* tool — it does **not** invent benchmark facts; if the source can't be verified it must
> return `INSUFFICIENT-EVIDENCE`.

---

## Controlled vocabulary (must match `enums`)
- **strength**: `direct` · `strong-proxy` · `weak-proxy` · `contested`  (NOT `indirect`)
- **basis**: `validated-against-downstream` · `face-validity-only` · `known-non-correlation`
- **coverage** (legal): `explicit` · `interpretive` · `contested`

## Strength rubric (from the md — use verbatim diagnostics)
- **direct** — what is scored *is* an instance of the harm/its defining capability.
  *Diagnostic: can you describe a high score as "the model did the harmful thing" with **no added
  assumptions**?* If yes → direct.
- **strong-proxy** — measures a near-necessary precursor/component; short, well-established chain,
  few confounds. *Diagnostic: is the measured thing a cause/necessary ingredient of the harm?*
- **weak-proxy** — correlated/suggestive across substantial inferential distance; multiple
  assumptions or obvious confounds (can score high without the harm, or vice versa). *Diagnostic:
  does the link rely on a chain of assumptions or a loose analogy?*
- **none** — if none of the above, the benchmark does not measure the harm.

**Hard rule:** `direct` is only defensible with basis `validated-against-downstream` **or** when
the score is *literally* an instance of the harm. `direct` + `face-validity-only` on a *societal
outcome* (e.g. market concentration, inequality) is almost always inflation → down-rate.

---

## The prompt (copy/paste)

```
You are validating one benchmark→harm mapping for an AI-risk evidence base. You are a careful
reviewer, not a benchmark author. Do NOT invent metrics, datasets, or results. If you cannot
verify what the source actually measures, return verdict = INSUFFICIENT-EVIDENCE.

INPUT
  benchmark_id:        {benchmark_id}
  benchmark_title:     {title}
  benchmark_evidence_type: {evidence_type}   # model benchmark | empirical study | index/assessment | tool
  what_it_measures:    {task + metric, in your own words from the source}
  harm_id / harm:      {harm_id} — {harm label + MIT subdomain}
  proposed strength:   {strength}
  proposed basis:      {basis}

STEP 1 — Is this actually a benchmark/eval?
  Does the source contain a real evaluation: a dataset, task, metric, eval suite, or model-card
  benchmark that produces a SCORE for a model? 
  - If it is a risk-framework / policy / position paper with NO evaluation → flag
    "NOT-A-BENCHMARK" and stop (it may still be valuable as empirical evidence, but it is not a
    benchmark→harm edge; route to the empirical-evidence track).

STEP 2 — Does the benchmark measure THIS harm?
  Apply the strength rubric diagnostics above. Decide: direct / strong-proxy / weak-proxy / none.
  - For socioeconomic/downstream harms (MIT 6.x labor, inequality, power), default to weak/strong
    proxy unless the score is literally an instance of the harm.

STEP 3 — Check strength vs basis consistency.
  - If strength = direct but basis = face-validity-only AND the harm is a societal outcome →
    DOWN-RATE (usually to weak-proxy or strong-proxy). 
  - strength = direct is only allowed with validated-against-downstream OR a score that is
    literally an instance of the harm.

STEP 4 — Enum check.
  - strength must be one of {direct, strong-proxy, weak-proxy, contested}. Reject "indirect".
  - basis must be one of {validated-against-downstream, face-validity-only, known-non-correlation}.

OUTPUT (JSON)
{
  "verdict": "VALID" | "DOWN-RATE" | "NOT-A-BENCHMARK" | "WRONG-HARM" | "INSUFFICIENT-EVIDENCE",
  "corrected_strength": "...",
  "corrected_basis": "...",
  "reason": "1-2 sentences citing the rubric diagnostic you applied",
  "confidence": "probable | possible | uncertain | tentative",
  "needs_human_review": true | false
}
```

---

## Worked checks (from this workbook)

| Edge | Expected verdict | Why |
|---|---|---|
| B259 *Market Concentration Implications of Foundation Models* → 6.1 Monopolisation, `direct`+FV | **DOWN-RATE → weak-proxy** | A macro-econ paper; no model score is an instance of monopolisation. Fails the "no added assumptions" test. |
| B248 *Correlated Errors in LLMs* → 6.1 Market concentration, `strong-proxy`+validated | **VALID** | Model-level measurement of correlated failure; a near-necessary ingredient of monoculture risk. |
| TheAgentCompany → 6.02.01 *Ability to automate jobs*, `strong-proxy`+FV | **VALID (pending source verification)** | Agentic task success is a near-necessary precursor capability; but `INSUFFICIENT-EVIDENCE` until the paper's tasks/metrics are confirmed. |
| Any edge with `strength = indirect` | **DOWN-RATE** | `indirect` is not a valid enum value (30 such edges exist). |

---

## Batch use
Run over an export of `bench_measures_harm` (e.g. filtered to `strength = direct` AND
`basis = face-validity-only`, which `outputs/coverage_by_domain.csv` counts per subdomain). Feed
each row through the prompt; collect `DOWN-RATE` / `NOT-A-BENCHMARK` rows into a review queue for
human sign-off. **Never auto-write the live sheet** — produce a proposed-changes file.
