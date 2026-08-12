# 13_f

## What this is
(Placeholder — Philip to confirm.) Likely: working with SEC 13F filings (institutional
holdings data). Update this section with the real goal before serious work starts.

## Conventions
- Python 3.14 (system default), native Windows — no WSL.
- Source data pulled from primary sources (SEC EDGAR first); cite URL + retrieval date
  for every external figure.
- Raw downloaded data goes in `data\raw\` (never edited); derived outputs in `data\out\`.
- Superseded files are archived, not deleted (firm-wide rule).

## Layout
- `src\` — code
- `data\raw\` — untouched source data (gitignored)
- `data\out\` — generated outputs (gitignored)
- `notes\` — working notes / findings
