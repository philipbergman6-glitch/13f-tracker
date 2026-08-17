# Phase 2: production release controls (2026-08-17)

Scope: make SEC ingestion production-safe before each quarterly publication.
Phase 1 (per-filer statuses + LATE/ERROR gate) is in commits ee9fe5d, c184f46.

## What was added

1. **`--force-refresh`** (`pipeline.py` → `edgar.list_13f_filings` →
   `common.fetch_cached(force=True)`): refetches mutable SEC indexes
   (submissions JSON) even when the cache was retrieved earlier the same day.
   SEC updates these in place continuously, so the day's first run otherwise
   hides filings that arrive later that day. Run with `--force-refresh`
   immediately before publication. Immutable accession documents are never
   refetched.
2. **Collision-safe raw snapshots**: a same-day re-refresh archives the
   superseded index under `data/raw/_archive/superseded/<retrieval-date>/`
   with a numeric suffix (`submissions.json.2`, …) instead of overwriting an
   earlier same-day archive. Unchanged bodies are restamped, not archived.
3. **Same-day-filing warning**: any in-window filing whose `filing_date` is
   today is listed loudly at the end of the run with a reminder to re-run
   `--force-refresh` before publishing (the index may still gain entries).
4. **Out-of-span filings**: a 13F filed for an in-window quarter outside the
   filer's `manager_map.csv` span (the monitored CIK 2038540 case) is flagged;
   a 13F-HR blocks that manager-quarter and fails the run (the map is stale),
   a 13F-NT warns only.
5. **Holdings validation** (`src/validate.py` → `data/out/validation.csv`):
   - ERROR (blocks the manager-quarter + fails the run): malformed CUSIP
     (not 9 alphanumeric), empty issuer, unparseable/negative value or
     shares, unknown `sh_prn_type`/`put_call`.
   - WARN (recorded only — every class occurs in accepted SEC filings,
     calibrated against the committed 2024Q2–2026Q2 history on 2026-08-17):
     CUSIP check-digit mismatch (2: SPDR 78462F953, AMRIZE H2627K103);
     implied price outside $0.001–$2,000,000 (BRK-A ~$750k is inside);
     issuer identity change — first-4-char prefix disagreement per CUSIP
     (17, incl. the genuine Amazon/Astera cross-labels 023135106/04626A103
     in Altimeter & Maverick 2024Q2 filings, and legit renames like
     CHESAPEAKE→EXPAND); QoQ share ratio >100x (17); QoQ implied-price
     ratio >10x (6, mostly the NFLX 2025Q4 10:1 split).
   - Current full run: **0 errors, 42 warnings**; all warnings reviewed,
     all explained by renames/splits/real trades except the Amazon/Astera
     cross-labels, which are filer-side errors in the original filings
     (our CSVs faithfully reproduce the filed rows).
6. **Run gate + dashboard protection**: every run writes
   `data/out/run_status.json` (ok/blocked/validation counts). `dashboard.py`
   hard-fails without touching `dashboard/index.html` when the last run
   failed (or no run exists); `--allow-failed-run` overrides after manual
   review. Verified live: flipping ok→false makes dashboard.py exit 1 with
   nothing written.

## Verification (2026-08-17)

- Test suite: 89/89 passing (`python3 -m unittest discover -s tests`),
  incl. new force-refresh, archive-collision, validation and gate tests.
- Full run `--start 2024Q2 --end 2026Q2 --skip-figi`: exit 0, 200 filings,
  178 CSVs, committed holdings + filer_status.csv byte-identical.
- `--force-refresh` run: all 21 submissions indexes refetched from
  data.sec.gov (retrieved 2026-08-17); every body identical upstream →
  restamped, no archive entries (correct: unchanged is not superseded).
