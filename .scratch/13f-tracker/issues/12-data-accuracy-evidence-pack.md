# 12 — Data-accuracy evidence pack for the boss review

Type: task (AFK)
Status: open
Blocked by: 10 (verify the final dataset the boss will see, i.e. post-Q2-2026 re-pull)

## Question

Execution ticket (map carries execution). Philip's boss must approve the data before
anything is pushed to TradingView; the approval needs evidence, not assertions. Ticket 08
already verified the backfill (179/180 row counts, live-EDGAR + Dataroma spot-checks
exact), but that evidence lives scattered across `data\out\` and ticket notes.

Produce one boss-readable verification document (Markdown in `notes\`, linked from the
dashboard or handed alongside it) covering the **final** dataset (post ticket-10 re-pull):

- Fresh independent spot-checks: for a sample of managers × quarters (including at least
  2 full-book checks and all 4 WhaleWisdom-only managers), re-derive holdings from live
  EDGAR and diff against the committed CSVs. Show the URLs, retrieval dates, and diffs.
- Manual Dataroma cross-check for a sample of the 16 Dataroma-covered managers
  (per ADR 0001: aggregators are QA cross-checks, never ingested).
- Row-count and portfolio-value reconciliation across all manager-quarters, including
  the known Lindsell Train cover-page discrepancy, stated plainly.
- CUSIP→ticker mapping coverage: current mapped/unmapped counts, what unmapped means
  for the dashboard and watchlists, and the override mechanism.
- Known limitations up front: 13F scope (US-listed longs only, no shorts/privates),
  filing lag, amendment handling, AUM-estimate caveats from ticket 04.

Resolution records: where the document lives and a one-line summary of any check that
did NOT come back clean (a check that fails blocks ticket 13, not silently).
