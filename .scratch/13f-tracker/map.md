# Wayfinder map: 13F tracker

Label: wayfinder:map
Created: 2026-08-12 (charting session)

## Destination

An automated, re-runnable quarterly pipeline in the `13_f` repo that, for the confirmed
20-manager list: (1) pulls and archives their 13F holdings with ≥8 quarters of history,
(2) generates a self-contained static HTML dashboard covering portfolio value vs external
AUM estimates, top positions, significant changes (new buys / adds / trims / exits),
industry-level patterns, and a cross-manager trend summary (stocks bought/sold by several
managers), and (3) maintains per-manager TradingView watchlists via the tradingview MCP.

**Execution override:** this map carries execution — tickets may build and deliver, not
only decide (confirmed by Philip 2026-08-12).

## Notes

- **The manager list (fixed, 2026-08-12, from Philip):**
  - WhaleWisdom-only per Philip (not on Dataroma): Situational Awareness, Altimeter
    Capital Management, Atreides Management, Coatue Management.
  - On Dataroma: Maverick Capital, Viking Global, Greenlight, Icahn, Fairholme,
    Pershing Square, Third Point, Berkshire Hathaway, Lone Pine, Appaloosa, Tiger Global,
    Giverny, Leon Cooperman, TCI, Fundsmith, Lindsell Train.
- **Dashboard content brief (Philip, 2026-08-12):** per manager — portfolio value
  (vs external total-AUM estimate), most significant positions, most significant changes
  (new purchases, significant increases/decreases, liquidations), industry patterns;
  plus a cross-manager summary table (stocks bought by several managers, sold by several).
- Dashboard form: static HTML, regenerated per quarter, versioned in repo.
- Cadence: recurring quarterly; archive ≥8 quarters of history.
- Git policy: commit parsed holdings tables + dashboard; raw downloads stay in
  gitignored `data\raw\` (re-fetchable from SEC).
- Watchlists: one per manager with a common prefix; existing "13F" watchlist on the
  account is left untouched.
- Sourcing (firm rule): primary sources first — SEC EDGAR is the presumed source of
  truth; Dataroma/WhaleWisdom as cross-check/enrichment. Final call is ticket 03.
- **Timing:** Q2-2026 13F deadline is 2026-08-14 (45 days after Jun 30) — two days after
  charting. Many managers file at the deadline; "latest" filings may be Q1 until then.
- TradingView MCP: installed at `Documents\coding_projects\TradingView\tradingview-mcp`,
  currently disconnected; launch quirk + gotchas in memory note `tradingview-mcp-setup`.
- Skills each session should consult: `/dataviz` for any dashboard/chart work;
  `/research` for AFK research tickets; `/grilling` + `/domain-modeling` for HITL tickets.
- **Approval gate (Philip, 2026-08-12):** Philip's boss must see the dashboard and the
  data-accuracy evidence and give an explicit go before anything is pushed to
  TradingView. Ticket 13 is the gate; tickets 06/07 sit behind it.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [05 — Dashboard prototype](issues/05-dashboard-prototype.md) — three-variant prototype on real Berkshire Q1-2026 EDGAR data (`prototypes\13f-dashboard-prototype.html`); Philip chose a **hybrid: variant C's cross-manager landing + variant A's report-style per-manager drill-down**, with written takeaways (2–3 sentences per manager) and full holdings behind an expand; content brief unchanged; **hard requirement: the real build must be genuinely a "$10,000 visually designed" dashboard** (prototype validated structure only, not styling). Build spun out as ticket 11.
- [08 — Build the EDGAR pull/parse pipeline and run the 8-quarter backfill](issues/08-build-edgar-pipeline-and-backfill.md) — built and backfilled 2026-08-12: `src\pipeline.py` (stdlib-only), 180 filings → 159 committed manager-quarter CSVs (all 20 managers, 8 quarters; SA 6 — all that exist), 139 change tables; 179/180 row counts match (the 1 mismatch is a Lindsell Train filer-side cover-page error); amendment semantics confirmed vs Form 13F Special Instruction 3; OpenFIGI free-tier confirmed, 1,047/1,173 CUSIPs mapped; live-EDGAR + Dataroma spot-checks exact. Q2-2026 re-pull spun out as ticket 10.

- [03 — Source of truth & schema](issues/03-source-of-truth-and-schema.md) — EDGAR-only (ADR 0001; aggregators = manual QA cross-checks, never ingested); one dashboard line per Manager via committed manager→CIK mapping; committed per-manager-quarter CSVs of quarter-final (post-amendment-merge) holdings; OpenFIGI CUSIP→ticker with committed cache; significant change = new buys/exits always, else ≥25% share-count change AND ≥0.5% of portfolio, or ≥1pp weight change — share counts, never value; options stored but kept out of the main book; backfill now, re-pull after 2026-08-14. Terminology in repo CONTEXT.md.
- [04 — AUM estimate sources](issues/04-aum-estimate-sources.md) — 15/20 have Form ADV RAUM (SEC monthly compilation, keyed on CRD; table + refresh recipe in notes/research/04-aum-sources.md); Berkshire & Icahn use 10-Q/8-K proxies; TCI press-only ($77.1bn end-2025); Cooperman no public figure — show 13F value only; RAUM is gross, label the column accordingly.
- [02 — Data-source landscape](issues/02-data-source-landscape.md) — EDGAR alone covers the need (8q×20 mgrs ≈ ~400 requests at 10 req/s w/ declared UA; XML schema + 13F-HR/A semantics verified live; DERA TSV bulk 2013Q2+); Dataroma covers all 16 listed managers w/ activity classification but forbids republishing; WhaleWisdom covers the 4 others, scraping banned, API free tier = trailing 8q minus current, $90/qtr for current — full facts in notes/research/02-data-source-landscape.md.
- [01 — Resolve managers to SEC filers](issues/01-resolve-managers-to-sec-filers.md) — all 20 resolved to active 13F filers (CIK table in notes/research/01-filer-resolution.md); 3 filer successions (Greenlight→DME, Appaloosa, Omega→Cooperman), 3 names with two active filers (Pershing Square, Fundsmith, Situational Awareness); Q2-2026 filed by only Lindsell Train as of 2026-08-12 — re-pull after 2026-08-14 deadline.

## Not yet specified

- Cross-manager trend analytics beyond the summary table (overlap scoring, sector
  rotation view). Deferred by Philip at ticket 05; sharpens after the first real
  dashboard build (ticket 11).
- Per-manager 8-quarter history charts (portfolio value, position count, top-position
  weights). Surfaced at ticket 05; sharpens once ticket 11's first build exists and
  ticket 10's re-pull lands Q2-2026.
- Watchlist update semantics: full sync (with deletions) vs additive; top-N vs all
  holdings; non-US-listed holdings mapping to TradingView symbols. Sharpens after
  tickets 01 + 06 (becomes ticket 07's input).

## Out of scope

- Trading, order placement, or any write to live trading/execution systems (firm rule —
  diagnostic and research only). TradingView watchlists are the boundary.
- Non-13F holdings coverage (short books, non-US positions, private holdings) — 13F only
  discloses US-listed long equity/options; the dashboard will say so, not fill the gap.
