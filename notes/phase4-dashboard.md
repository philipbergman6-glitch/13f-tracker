# Phase 4: executive-dashboard finish (2026-08-17)

Presentation/labeling refinement pass on the existing dashboard — desktop
aesthetic preserved, no displayed holdings numbers changed. Success criteria
defined before coding (mirrored in .scratch/phase4-success-criteria.md).

## What changed

1. **Mobile overflow fixed** (`dashboard_template.html`): header + status
   strip flex-wrap; a ≤640px media query (tighter padding, left-aligned hero,
   full-width hero tile, narrower bar-row grid columns). Wide tables keep
   their intentional panel-internal horizontal scroll.
2. **Combined value relabeled**: hero now reads "sum of reported 13F long
   values" + "overlapping across books — not firm AUM, not investable
   capital"; matching methodology bullet in the footer.
3. **Largest move ranked by dollar magnitude** (`dashboard.py`):
   `move_magnitude_usd` — new = current value; exit = prior-quarter value
   (prev weight × prev book); add/trim = |Δshares| × current implied price
   (labelled "estimated" in the sentence). Fixes e.g. Berkshire 2026Q2,
   where a $580k new DHI position headlined over an $8.77bn GOOGL add.
   13 of 20 managers' takeaway headlines changed; all other payload data
   verified byte-identical vs the previous build (see Verification).
4. **Consensus shortened**: display capped at 6 rows per side with an
   explicit "+N more consensus names not shown" line (no silent truncation);
   ordering unchanged (manager count desc, then combined $ desc =
   conviction first). 2026Q2 shows 6 of 19 buys / 6 of 13 sells.
5. **Methodology without hover**: bar-row tooltips now also open on tap
   (click) and close on tap-outside; keyboard focus already worked. All
   tooltip-only facts also exist in visible text (full-holdings table,
   footer methodology incl. new bullets for the combined total, QoQ deltas,
   and largest-move definition).
6. **Footer refreshed**: removed the stale hardcoded "Q2 2026 filings (due
   2026-08-14) enter after the post-deadline re-pull" sentence; generation
   line now uses a full UTC timestamp.
7. **Run-status strip** (new, under the masthead): "Data through <quarter> ·
   Generated <UTC timestamp> · checks passed/failed/unknown (errors ·
   warnings) · pipeline run <UTC>" — built from data/out/run_status.json at
   build time via `run_status_summary()` (passed/failed/unknown states,
   nothing hardcoded); repeated in the footer's Data column.

## Verification (2026-08-17)

- Tests: 121/121 (`python3 -m unittest discover -s tests`); new coverage for
  move magnitudes, largest-move ranking (tiny-new never beats billion-dollar
  add/exit), and run-status summary states (ok / failed / missing).
- Regenerated via the normal gated path (`python3 src/dashboard.py`, run
  gate active): 626 KB, as of 2026Q2, 20 managers.
- Payload diff old→new: all stats/holdings/changes/consensus values
  identical; only takeaway sentences + generation metadata differ, plus one
  pre-existing staleness — the committed index.html predated c184f46's
  manager-map fix, so filer 2038540 no longer lists under Situational
  Awareness 2026Q2 (correct per the map; not a Phase 4 change).
- Overflow, measured in headless Chrome (iframe harness reporting
  scrollWidth, since headless Chrome clamps top-level windows to 500px):
  landing + berkshire + coatue pages at 1440/1280/1024/768/390/360 → no
  page-level horizontal overflow at any width. Control: the pre-Phase-4
  dashboard overflows at 360 (scrollWidth 383–388), confirming the harness
  detects real overflow. Screenshots reviewed at all six widths.
- `git status`: only src/dashboard.py, src/dashboard_template.html,
  tests/test_dashboard.py, dashboard/index.html modified; data/holdings/**
  and filer_status.csv untouched.
