# 11 — Build the production dashboard ("$10,000" visual bar)

Type: task
Status: open — built 2026-08-12, awaiting Philip's HITL sign-off on the visual bar
Blocked by: — (08 resolved; can build on the backfill now — regenerate after ticket 10's
re-pull lands Q2-2026 data)

## Question

Execution ticket (map carries execution). Build the real static-HTML dashboard per
ticket 05's resolved design:

- **Skeleton:** hybrid — cross-manager landing (consensus buys/sells + 20 manager
  cards) with variant-A report-style drill-down per manager (hero tiles incl. 13F
  value vs AUM per ticket 04, top positions, significant changes, sector mix, full
  holdings behind an expand). See `prototypes\13f-dashboard-prototype.html` for the
  validated structure — structure only, not the styling.
- **Written takeaways:** 2–3 generated sentences per manager per quarter; every number
  in them traced to the committed CSVs (firm rule: no unsourced figures).
- **Visual bar (Philip, 2026-08-12): genuinely a "$10,000 visually designed"
  dashboard.** Design is a first-class deliverable — invoke `/dataviz` AND
  `/artifact-design`-grade typography/spacing/color discipline; light+dark; this is
  the section Philip will judge hardest.
- Data from the pipeline's outputs — the committed `data\holdings\` and `data\ref\`
  (incl. the ticket-04 AUM table), plus `data\out\changes\`, which is gitignored and
  regenerated locally; real sector mapping (committed ref table, not the
  prototype hand-map); cross-manager table computed from all 20 managers — no mock
  content anywhere.
- Output: self-contained HTML versioned in the repo per map Notes; regenerated per
  quarter by `src\pipeline.py` or a sibling entry point.

Resolution records: where the dashboard lives, the regeneration command, and
Philip's acceptance that the visual bar is met (HITL sign-off on the finished look).

## Progress (2026-08-12)

Built and committed; **Philip's visual sign-off is the only open item.**

- **Where it lives:** `dashboard\index.html` (committed, self-contained, 592 KB —
  works by double-click, no network). Landing = consensus buys/sells + 20 manager
  cards; per-manager report pages via hash routes (`#/m/<slug>`).
- **Regeneration:** `python src\dashboard.py` (after each quarterly
  `python src\pipeline.py` run; `python src\sectors.py` first if new CUSIPs).
  `--quarter 2026Q1` pins the as-of quarter; default = latest quarter common to
  the manager list.
  One prerequisite is easy to miss: the dashboard reads `data\out\changes\`,
  which is **gitignored**, so a fresh clone has no change tables and would
  render every manager as having no significant changes. `python src\changes.py`
  rebuilds all 139 of them offline from the committed holdings CSVs in seconds
  (verified 2026-08-12: byte-identical to the existing tables), and
  `pipeline.py` calls it as its own step 5.
- **New committed inputs built for this ticket:**
  - `data\ref\aum.csv` — ticket-04 AUM table as data (Fundsmith + Cooperman have
    empty figures with honest notes, per ticket 04).
  - `data\ref\sectors.csv` — real sector map: CUSIP→ticker→CIK→SIC (SEC EDGAR
    submissions API), SIC→GICS-style rollup defined in `src\sectors.py`.
    Value-weighted unclassified: 0.32% of latest-quarter books.
  - `data\ref\sector_overrides.csv` — 17 hand-resolved foreign-CINS issuers
    (OpenFIGI has no match); each row's CIK is verified against the EDGAR entity
    name at fetch time (caught the Fidelis→Pelagos rename 2026-05-07).
  - 81 ticker overrides written into `data\ref\cusip_ticker.csv` (US listings for
    CUSIPs whose FIGI best-match was a foreign line, e.g. Chevron CHV→CVX,
    Moody's DUT→MCO); holdings CSVs regenerated with `--skip-figi`.
- **Takeaways:** 2–3 deterministic template sentences per manager, computed from
  the same committed CSVs as the tiles (verified: Berkshire $263.1bn / 29
  positions / 16 exits / MSFT sold by 10 of 20 / combined $496.3bn all re-derive
  exactly from `data\holdings` + `data\out\changes`).
- **Design:** /dataviz method followed (single-hue bar lists, meter with same-ramp
  track, palette validated light+dark via validate_palette.js, action chips are
  glyph+word not color-alone, every chart value also in a table); typography =
  embedded Newsreader (OFL, data-URI) + system sans; light+dark themes with
  manual toggle; visually QA'd in Chrome both themes.
- **Tests:** `tests\test_dashboard.py`, 25 unittest cases over the shaping seams
  (formatting, stats, consensus, sector mix, takeaways, quarter pinning), plus
  `tests\test_figi.py`, 11 offline cases over the OpenFIGI batching seam
  (batching, job shape, 429 back-off, cache hits/misses/overrides) — 36 in all,
  green; full suite + compileall pass.
- **Fix (2026-08-12): `--quarter` did not pin.** The per-manager fallback in
  `build_payload` used the manager's newest quarter outright, so a pin earlier
  than a manager's first filing walked *forward* — `--quarter 2024Q3` showed
  Situational Awareness (first tracked 2024Q4) at 2026Q1, and because
  `later_filing` compares latest-vs-shown it came back `None`, so the "pinned
  to…" banner stayed silent. Knock-on: those 2026Q1 changes were pooled into the
  2024Q3 consensus (2 rows — AMD and TSM buys). Fallback is now the manager's
  latest quarter at or before the as-of date, and a manager with no book that old
  is left off. Covered by `TestPinnedQuarter` (3 cases, all red before the fix).
  Unpinned output is unchanged — 2026Q1, 20 managers, payload byte-identical —
  so the committed `dashboard\index.html` did not need regenerating.
- **Cleanup (2026-08-12), no behaviour change.** Post-build review pass over the
  code this ticket added:
  - Dead `CHANGE_COLUMNS` import dropped from `dashboard.py`; function-local
    imports (`base64` in `render`, `time`/`urllib.request`/`Counter` in
    `sectors.py`) hoisted to module level.
  - `common_quarter` → `as_of_quarter` (it returns the dashboard's as-of
    quarter; "common" read as "ordinary"). `load_aum` → `load_aum_by_manager`,
    and the payload's stuttering `aum.aum_usd` → `aum.usd` (template updated to
    match; the `aum_usd` column name in `data\ref\aum.csv` is unchanged).
  - **Seam: one OpenFIGI batcher.** `figi.resolve` and
    `sectors.us_ticker_lookup` each had their own copy of the batch-to-10,
    POST, retry-on-429, pace loop. Both now go through `figi.map_batch`, which
    yields one `[(cusip, result)]` list per request so callers keep their own
    checkpointing and progress reporting; `exch_code="US"` is what the sectors
    path passes instead of forking the loop. `figi.best_match` names the
    "first match or {}" idiom both sides open results with.
  - **Seam: `SectorRefresh`.** `(rows, figi_cache, cik_map, today)` was threaded
    through four `sectors.py` functions in three different subsets. They are now
    methods on a `SectorRefresh` dataclass built by `SectorRefresh.load()`, with
    `save()` naming the "write both the sector rows and the FIGI cache" pairing
    that each step had been open-coding.
  - Evidence: `build_payload()` output is byte-identical to the pre-cleanup code
    modulo the deliberate `aum.usd` rename (20 managers, 2026Q1, combined
    $496,282,910,431); `python src\sectors.py` rewrites `sectors.csv` and
    `cusip_ticker.csv` byte-identically; 36/36 tests and compileall pass.
  - `dashboard\index.html` was regenerated so the committed artifact still
    matches its generator. The diff is 5 lines — the 4 template lines carrying
    the `aum.usd` rename and the embedded data blob — and the rendered page is
    unchanged.
- Q2-2026: regenerate after ticket 10's re-pull (Lindsell Train's early Q2 filing
  is on record; dashboard pins to 2026Q1 and says so on their page).

## Resolution

Two of the three records are closed; the third is Philip's to give.

1. **Where the dashboard lives** — `dashboard\index.html`, committed and
   self-contained (592 KB, opens by double-click, no network). Landing =
   consensus buys/sells + 20 manager cards; per-manager report pages on
   `#/m/<slug>` hash routes.
2. **Regeneration command** — from the repo root:

   ```
   python src\pipeline.py     # quarterly: fetch, parse, merge, write holdings + change tables
   python src\sectors.py      # only if the quarter brought new CUSIPs
   python src\dashboard.py    # writes dashboard\index.html
   ```

   On a fresh clone (or any tree where `data\out\` is empty), run
   `python src\changes.py` before `dashboard.py` — `data\out\changes\` is
   gitignored and the dashboard reads it. Add `--quarter <YYYYQn>` to pin the
   as-of quarter; the default is the quarter most managers have last filed.
3. **Visual bar met — OPEN.** Needs Philip's HITL sign-off on the finished look
   (the "$10,000 visually designed" bar from ticket 05). Nothing in this ticket
   can close it; ticket 13's boss review waits on it.

**Working-tree state (2026-08-12):** everything above except the original build
is uncommitted — the `--quarter` pinning fix, `TestPinnedQuarter`, the cleanup
pass, `tests\test_figi.py`, and the regenerated `dashboard\index.html`. Also
untracked: `prototypes\13f-dashboard-prototype.html` (ticket 05's validated
structure, referenced by this ticket) and `dashboard\GEMS-13F-Q1-2026.html` — a
copy of the committed dashboard under a sharing-friendly name, line-for-line
identical to it, differing only in CRLF line endings. Whether
those last two belong in the repo is Philip's call — the map's git policy names
holdings tables and the dashboard, not prototypes or export copies.
