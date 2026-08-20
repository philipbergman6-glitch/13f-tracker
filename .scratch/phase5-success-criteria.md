# Phase 5 success criteria (defined before coding, 2026-08-17)

Goal: codify the existing controls into one formal, repeatable publication
sequence with automatic blocking. No existing gate is re-implemented or
weakened — release.py calls pipeline.py / unittest / dashboard.py / evidence.py
and adds only the publish/rollback gates that don't exist yet.

## Expected outputs
1. `src/release.py` — subcommands:
   - `stage --quarter Q [--start --end --skip-figi]`: steps 1–6
     (pipeline --force-refresh → test suite → dashboard to
     `dashboard/staging/index.html` → evidence package with `--dashboard`
     pointing at staging). Stops at first non-zero exit.
   - `publish --quarter Q`: steps 8–9. Refuses unless ALL of:
     run_status ok · tests pass (fresh run) · evidence package exists for Q
     and manifest.pipeline_run matches current run_status (not stale /
     regenerated) · every checksum in the package matches the artifact on
     disk (incl. staging dashboard) · no filer status LATE/ERROR · every
     filings.csv row has retrieved_date + filing_url (provenance) · sign-off
     block filled, ISO date, decision starts "approve", and report.md
     committed in git. Then: archive prior `dashboard/index.html` +
     `dashboard/release.json` to `dashboard/_archive/<UTC>/`, copy staging →
     published, write `dashboard/release.json`, append `docs/releases.csv`.
   - `rollback [--to <stamp>]`: archive current published, re-promote the
     chosen (default newest) archived release, record in releases.csv.
2. `src/evidence.py` — `--dashboard` arg (default unchanged), sign-off block
   with explicit instructions + YYYY-MM-DD field, reproduce section uses
   release.py, report references the actual dashboard path. No gate removed.
3. `docs/release-runbook.md` — sequence, block conditions, sign-off
   procedure, rollback, audit-trail queries.
4. `tests/test_release.py` — every publish gate trips on its condition and
   the happy path passes; promote archives-not-deletes; rollback restores.
5. `.gitignore` +`dashboard/staging/`; `notes/phase5-release-governance.md`.

## Success criteria (verify before committing)
- Full test suite passes (121 existing + new release tests, 0 failures).
- `python3 src/release.py stage --quarter 2026Q2 --skip-figi` exits 0 on the
  real repo: staging dashboard written, evidence package regenerated for
  2026Q2 (old one archived under docs/evidence/_archive/), pipeline ran with
  --force-refresh.
- `python3 src/release.py publish --quarter 2026Q2` on the real repo REFUSES
  (exit 1) with a clear sign-off message; `dashboard/index.html`,
  releases.csv untouched.
- In a sandbox copy of the repo: fill sign-off + commit → publish succeeds;
  `dashboard/index.html` == staging bytes; prior dashboard archived (not
  deleted); releases.csv + dashboard/release.json answer "what was published
  when, from which run". Then rollback restores the prior bytes and archives
  the rolled-back copy.
- Real repo: committed holdings CSVs + filer_status.csv byte-identical after
  the stage run (unless a genuinely new SEC filing arrived — report if so).
- No interactive prompts anywhere; every gate is a hard SystemExit.
