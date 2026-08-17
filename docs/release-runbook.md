# Quarterly release runbook

The formal publication sequence for the 13F tracker. Every step is
non-interactive; every gate is a hard failure (exit ≠ 0, nothing published).
The orchestrator is `src/release.py`; it sequences the existing controls
(pipeline gates, test suite, dashboard run-gate, evidence-package gates) and
adds the staged→published promotion. Superseded files are archived, never
deleted (firm-wide rule).

## Locations

| What | Path | Committed |
|---|---|---|
| Published dashboard (the release) | `dashboard/index.html` | yes |
| Live release record | `dashboard/release.json` | yes |
| Staging dashboard (pre-approval build) | `dashboard/staging/index.html` | no (gitignored) |
| Archived prior releases | `dashboard/_archive/<UTC>/` (`index.html` + `release.json`) | yes |
| Evidence package for quarter Q | `docs/evidence/<Q>/` (superseded → `docs/evidence/_archive/`) | yes |
| Release log (append-only) | `docs/releases.csv` | yes |

## Sequence

1–6. **Stage** — `python src/release.py stage --quarter <Q> [--skip-figi]`
   Runs, stopping at the first failure:
   1. `pipeline.py --force-refresh` — refreshes mutable SEC indexes,
      downloads + archives new filings into `data/raw/`, builds holdings and
      change datasets. Its gates: LATE/ERROR filer statuses, row-validation
      ERRORs, out-of-span 13F-HRs all fail the run.
   2. Full test suite (`python -m unittest discover -s tests`).
   3. `dashboard.py --quarter <Q> --out dashboard/staging/index.html` — the
      published copy is never touched at this step (and dashboard.py itself
      refuses to build over a failed run).
   4. `evidence.py --quarter <Q> --dashboard dashboard/staging/index.html` —
      builds `docs/evidence/<Q>/`. Its gates: failed/stale pipeline run,
      failing tests, reconciliation mismatch without a
      `data/ref/known_exceptions.csv` entry, missing raw source data /
      retrieval dates, incomplete filer-status coverage.

7. **Review + sign-off (human)** — review the staging dashboard and
   `docs/evidence/<Q>/report.md`. To approve: fill the three sign-off lines
   at the end of the report (name; date as YYYY-MM-DD; decision beginning
   `approve`), then **commit the signed report**. Approval lives in git
   history. Regenerating the package rewrites the block blank, so an
   approval can never carry over to changed data.

8–9. **Publish** — `python src/release.py publish --quarter <Q>`
   Re-verifies every gate (below), then: archives the current
   `dashboard/index.html` + `release.json` to `dashboard/_archive/<UTC>/`,
   copies staging → `dashboard/index.html`, writes `dashboard/release.json`,
   appends `docs/releases.csv`. Then commit the published dashboard, the
   archive, `release.json` and `releases.csv` together.

## Publish gates (any one blocks with exit 1, nothing modified)

- Last pipeline run missing or not ok (`data/out/run_status.json`).
- Test suite fails (run fresh at publish time).
- No evidence package for `<Q>`, or its `manifest.json` cites a different
  pipeline run than the current `run_status.json` (stale / regenerated data).
- Any artifact digest differs from the package's `checksums.csv` (holdings,
  ref tables, change tables, run outputs, staging dashboard) — the output
  being published must be byte-for-byte the reviewed one.
- Any filer status is LATE or ERROR (unexplained absence / failure).
- Any filing in `filings.csv` lacks a source URL or retrieval date
  (missing provenance).
- Staging dashboard missing or not as-of `<Q>`.
- Sign-off block blank, malformed, not an approval, or the signed report is
  not committed.

## Rollback

`python src/release.py rollback [--to <stamp>]` re-promotes the newest (or
named) archived release from `dashboard/_archive/`:
the currently published copy is archived first (nothing lost), the archived
`index.html` + its `release.json` are restored, and an `action=rollback` row
is appended to `docs/releases.csv`. Commit the result. The archive entry
that was restored stays in place.

## Audit trail — "what was published on date X, from which run?"

- `docs/releases.csv`: the row with the latest `published_utc` ≤ X. Each row
  records quarter, pipeline-run timestamp, source commit, dashboard SHA-256,
  evidence package + generation time, reviewer, review date, decision, and
  where the prior release was archived.
- `dashboard/release.json` describes what is live right now.
- `docs/evidence/<Q>/` (or its `_archive/`) holds the full evidence for that
  release: filings with SEC URLs + retrieval dates, reconciliation, merge
  decisions, statuses, tests, checksums, and the committed sign-off.
- Git history of `dashboard/index.html` cross-checks the same story.
