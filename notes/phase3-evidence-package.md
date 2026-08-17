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

## Verification (2026-08-17)

1. Test suite: **111/111 passing** (`python3 -m unittest discover -s tests`;
   89 pre-existing + 22 new merge-decision / verification / evidence tests).
2. Full run `--start 2024Q2 --end 2026Q2 --skip-figi`: exit 0, 200 filings,
   178 CSVs; `git status data/holdings` clean — committed holdings CSVs and
   `filer_status.csv` byte-identical. Cover-page check now reports rows
   199/1 and value totals 3 mismatches.
3. `python3 src/evidence.py --quarter 2026Q2` → `docs/evidence/2026Q2/`
   (10 files); report.md carries the item→file checklist for all 10 required
   items, a reproduce section pinned to the source commit, and a blank
   reviewer sign-off. 201 filings in filings.csv (200 parsed HR + 1 NT), 349
   checksummed source files + dashboard SHA-256.
4. Reconciliation mismatches are exactly the three expected —
   Lindsell Train 2025Q1 (rows 29/28, value $3,614,010,966/$4,000,701,335),
   Situational Awareness 2025Q4 (−$1), TCI 2025Q3 (+$1) — each annotated
   with its EXC id; removing an exception row makes evidence.py exit with
   the mismatch details (covered by tests/test_evidence.py).
5. Hard-fail gates unit-tested: failed/missing run, missing merge decision,
   unmapped CIK, missing status row, status accession absent from the
   verification table, mismatch without exception.
6. Superseding verified live: regenerating archived the prior draft to
   `docs/evidence/_archive/2026Q2/20260817T164158Z/` before rewriting.
   Archives of never-committed drafts stay on disk untracked; an archive of
   a previously committed package should be committed alongside its
   replacement.
