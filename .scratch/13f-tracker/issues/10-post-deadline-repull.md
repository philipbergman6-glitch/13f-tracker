# 10 — Post-deadline Q2-2026 re-pull (live test of the late-filing path)

Type: task
Status: open
Blocked by: none (actionable from 2026-08-15)

## Question

Execution ticket, spun out of ticket 08's mandate. After the 2026-08-14 Q2-2026
deadline, re-run `python src\pipeline.py --start 2024Q2 --end 2026Q2` and verify:

- All 20 managers now have a 2026Q2 holdings CSV (or a flagged explanation — e.g.
  a filer that went 13F-NT or filed late).
- Row-count verification stays clean; any new amendment chains merge without flags.
- Change tables for 2026Q2 look sane (this is the first quarter-pair produced by a
  true incremental run rather than backfill).
- Commit the new CSVs + updated `data\ref\cusip_ticker.csv`.

This is the live test of the amendment/late-filing path called for by ticket 03's
decision 8. Record anything the backfill path didn't exercise.
