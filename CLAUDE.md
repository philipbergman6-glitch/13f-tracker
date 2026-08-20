# 13_f

## What this is
Quarterly 13F tracker for a fixed 16-manager list: EDGAR-only pipeline (ADR 0001) that
builds quarter-final holdings CSVs, a static HTML dashboard, and per-manager TradingView
watchlists. Terminology in CONTEXT.md; decisions in `.scratch\13f-tracker\` (wayfinder map).

## Conventions
- Python 3.14 (system default), native Windows — no WSL.
- Source data pulled from primary sources (SEC EDGAR first); cite URL + retrieval date
  for every external figure.
- Raw downloaded data goes in `data\raw\` (never edited); derived outputs in `data\out\`.
- Superseded files are archived, not deleted (firm-wide rule).

## Layout
- `src\` — code (`pipeline.py` is the entry point; quarterly publication goes
  through `release.py` — stage → human sign-off → publish, see
  `docs\release-runbook.md`)
- `dashboard\index.html` — the published dashboard (promoted from
  `dashboard\staging\`, gitignored); prior releases in `dashboard\_archive\`;
  release log in `docs\releases.csv`
- `data\raw\` — untouched source data (gitignored)
- `data\out\` — generated outputs incl. change tables + verification (gitignored)
- `data\holdings\<manager>\<YYYYQn>.csv` — committed quarter-final holdings
- `data\holdings\filer_status.csv` — committed per-filer quarterly status
  (HOLDINGS / NT / DUPLICATE / NOT_DUE / LATE / ERROR); LATE or ERROR blocks
  publication of that manager-quarter and fails the pipeline run
- `data\out\validation.csv` + `data\out\run_status.json` — per-run validation
  findings and run outcome; validation ERRORs block publication, and
  `dashboard.py` refuses to rebuild over a failed run
- `data\ref\` — committed reference tables (manager map, CUSIP→ticker cache)
- `notes\` — working notes / findings
- `docs\adr\` — architecture decision records
