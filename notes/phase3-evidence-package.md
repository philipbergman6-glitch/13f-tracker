# Phase 3: auditable validation package (2026-08-17)

Scope: every quarterly release generates a committed, self-contained evidence
package that lets another analyst reproduce the dashboard and explain every
displayed number without temporary files. Phases 1-2: ee9fe5d, c184f46, 04122a4.

## Expected outputs (defined before coding)

New committed package per release at `docs/evidence/<YYYYQn>/`:

- `report.md` — human-readable report covering the 10 required items, a
  "how to reproduce this release" section, and a blank reviewer sign-off block.
- `filings.csv` — every filing used (13F-HR incl. amendments, plus 13F-NT
  notices): manager, quarter, CIK, filer name, form, accession, filing date,
  report period, SEC URL, raw-data retrieval date, merge role, parsed row
  count vs cover-page tableEntryTotal, parsed value sum vs tableValueTotal,
  match flags.
- `merge_decisions.csv` — per filing: why it is / is not part of the
  quarter-final book (base original / restatement / new-holdings / superseded
  / excluded), plus cross-filer duplicate drops.
- `filer_status.csv`, `validation.csv`, `flags.csv` — copies of the run's
  gate outputs (multi-filer completeness + validation findings).
- `exceptions.csv` — copy of the committed `data/ref/known_exceptions.csv`.
- `test_results.json` — suite name, test count, pass/fail, run timestamp.
- `checksums.csv` — SHA-256 of `dashboard/index.html` and every data file it
  derives from (holdings CSVs, filer_status, ref tables, change tables, run
  gate outputs).
- `manifest.json` — run metadata: run_status.json content, source git commit
  (+ dirty state), release quarter, window, generation timestamp, file list.

Pipeline changes feeding it (all consolidation, no re-derivation):

- `build.write_rowcount_verification` extended: filing_date, report_date,
  parsed value sum, tableValueTotal, value match, SEC URL columns
  (`data/out/verification_rowcounts.csv` schema grows; regenerated scratch).
- `build.merge_quarter` / `dedupe_filers` decisions recorded to
  `data/out/merge_decisions.csv` at run time.
- New committed `data/ref/known_exceptions.csv`: durable register of accepted
  filer-side discrepancies with resolutions and source citations.
- New `src/evidence.py`: consolidates the above into the package; superseded
  packages archived to `docs/evidence/_archive/`, never deleted.

## Success criteria

1. `python3 -m unittest discover -s tests` passes (89 existing + new tests).
2. Full run `python3 src/pipeline.py --start 2024Q2 --end 2026Q2 --skip-figi`
   exits 0; committed holdings CSVs + `filer_status.csv` byte-identical.
3. `python3 src/evidence.py --quarter 2026Q2` produces a package complete
   against all 10 required items (checklist in report.md maps item -> file).
4. Hard-fail behaviour: evidence generation refuses to run over a failed or
   missing pipeline run, a failing test suite, a missing dashboard, missing
   raw data (no retrieval date), or a cover-page reconciliation mismatch that
   has no entry in `known_exceptions.csv`.
5. Every rows/value mismatch in `filings.csv` maps to a known exception:
   expected mismatches are exactly Lindsell Train 2025Q1 (rows + value),
   Situational Awareness 2025Q4 ($1), TCI 2025Q3 ($1).
6. Re-running evidence.py archives the previous package before rewriting.

## Verification

(filled in after implementation — see bottom of file)
