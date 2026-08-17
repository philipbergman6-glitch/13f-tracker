# Phase 5: release governance (2026-08-17)

Codifies the existing controls (Phases 1–4) into one formal, repeatable
publication sequence with automatic blocking. No existing gate was rebuilt or
weakened — `src/release.py` sequences pipeline.py / the test suite /
dashboard.py / evidence.py and adds only the staged→published promotion.
Success criteria defined before coding (.scratch/phase5-success-criteria.md);
operating doc: `docs/release-runbook.md`.

## What was added

1. **`src/release.py`** — three subcommands:
   - `stage --quarter Q`: steps 1–6 (pipeline `--force-refresh` → full test
     suite → dashboard built to `dashboard/staging/index.html`, never the
     published copy → evidence package checksummed against the staging
     build). Stops at the first non-zero exit.
   - `publish --quarter Q`: steps 8–9. Hard-fails unless: green pipeline
     run; tests pass (fresh); evidence package exists for Q and cites the
     current pipeline run (stale/regenerated packages block); every
     `checksums.csv` digest matches the artifact on disk (the published
     output is byte-for-byte the reviewed one); no LATE/ERROR filer status;
     every filing has a source URL + retrieval date; staging dashboard is
     as-of Q; sign-off block filled (ISO date, decision begins `approve`)
     and the signed report committed. Then archives the prior
     `dashboard/index.html` + `release.json` to `dashboard/_archive/<UTC>/`,
     promotes staging, writes `dashboard/release.json`, appends
     `docs/releases.csv` (append-only release log).
   - `rollback [--to <stamp>]`: archives the current published copy, then
     re-promotes an archived release; recorded as `action=rollback`.
2. **Sign-off mechanism**: reviewer fills the three-line block at the end of
   `docs/evidence/<Q>/report.md` and commits it. evidence.py owns the
   template (`SIGN_OFF_LINES`), release.py owns the parsing regexes; a test
   asserts the template parses as blank, so they cannot drift. Regenerating
   the package rewrites the block blank and any pipeline re-run changes
   `run_status.json`, so an approval can never carry over to changed data.
3. **evidence.py**: `--dashboard` arg (release.py points it at staging;
   default unchanged), parameterized `dashboard_as_of()`, reproduce section
   now cites `release.py stage`, sign-off block gained instructions and a
   YYYY-MM-DD date field.
4. `dashboard/staging/` gitignored; runbook at `docs/release-runbook.md`;
   CLAUDE.md layout updated.

## Verification (2026-08-17)

- Tests: 145/145 (121 existing + 24 new in `tests/test_release.py` — every
  publish gate trips on its condition; promote archives-not-deletes;
  rollback restores; template/regex drift guard).
- Live `release.py stage --quarter 2026Q2 --skip-figi`: exit 0 — pipeline
  with `--force-refresh` (200 filings, 0 validation errors, 42 reviewed
  warnings, statuses DUPLICATE=1 HOLDINGS=191 NT=1), 145 tests, 626 KB
  staging dashboard as-of 2026Q2, evidence package regenerated (prior
  archived under `docs/evidence/_archive/2026Q2/`). Committed holdings CSVs
  and `filer_status.csv` byte-identical after the run.
- Live `release.py publish --quarter 2026Q2` on the real repo: **refused**
  (exit 1, "sign-off 'reviewer' is blank"), nothing modified.
- Full rehearsal in a sandbox copy: sign-off filled + committed → publish
  succeeded (staging sha promoted to `dashboard/index.html`, prior sha
  archived, `docs/releases.csv` + `dashboard/release.json` written with
  quarter / run / commit / digests / reviewer); `rollback` restored the
  prior bytes exactly, retained both archive entries, appended a rollback
  row.
- Real repo state after Phase 5: 2026Q2 is **staged, not published** —
  awaiting the human sign-off in `docs/evidence/2026Q2/report.md` before
  `python src/release.py publish --quarter 2026Q2`.
