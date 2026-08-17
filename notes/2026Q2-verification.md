# 2026Q2 data verification (retrieved & verified 2026-08-17)

Scope: all 20 managers, quarters 2024Q2–2026Q2 (200 filings, 178 holdings CSVs).
Method: (1) internal reconciliation of every holdings CSV against the SEC filing's own
cover page; (2) external corroboration of headline Q2 moves against press coverage.

## 1. Reconciliation vs SEC cover pages

For every (filer, accession): recomputed row count and total value from our
`data/holdings/` CSVs and compared to `tableEntryTotal` / `tableValueTotal` in the
filing's `primary_doc.xml` (source: EDGAR, retrieved 2026-08-17).

- **2026Q2: 21/21 filings exact match** — row counts and dollar totals to the dollar.
- All quarters: 197/200 exact. The 3 exceptions are filer-side errors, never amended:
  - Lindsell Train 2025Q1 (acc 0001172661-25-001932): cover page declares 28 entries /
    $4,000,701,335; the filed info table contains 29 unique-CUSIP entries summing
    $3,614,010,966. Our data matches the filed table (authoritative holdings list).
  - Situational Awareness 2025Q4 (acc 0002045724-26-000002): cover total $1 below table sum.
  - TCI 2025Q3 (acc 0001647251-25-000014): cover total $1 above table sum.
- Amendment flags: clean; no unprocessed 13F-HR/A.
- Pershing Square: LP entity (CIK 1336528) filed 13F-NT for Q2; holdings are in
  Pershing Square Inc.'s (CIK 2026053) combined 13F-HR — 15 rows / 14 positions is complete.

## 2. External corroboration (press, retrieved 2026-08-17)

Our figure → independent source, all matched:

- Atreides SpaceX $4,670,106,641 / portfolio $14.3B, 49 positions → Dealroom Q2 13F note
  (https://app.dealroom.co/news/note/q2-2026-13f-comparison-atreides-management-and-altimeter-capital)
- SpaceX (SPCX) 13F-reportable: Nasdaq IPO 2026-06-12 → CNBC, Bloomberg
  (https://www.cnbc.com/2026/05/20/spacex-ipo-live-updates.html)
- Cerebras (CBRS) 13F-reportable: Nasdaq IPO 2026-05-14 → CNBC
  (https://www.cnbc.com/2026/05/14/cerebras-cbrs-stock-trade-nasdaq-ipo.html)
- Coatue new SpaceX / Intel (12.1M sh) / Cerebras (13G: 7,011,028 sh) → Reuters via
  TradingView; StockTitan 13G. Press confirms positions; exact dollar values are from
  the EDGAR filing itself (press did not publish them).
- Pershing Square $19,465,692,772, 14 positions, new V/MA/SPGI/NFLX → Seeking Alpha
  (https://seekingalpha.com/article/4937160-tracking-bill-ackmans-pershing-square-13f-portfolio-q2-2026-update)
- Berkshire $299,253,556,246, 29 unique CUSIPs, new DHI toehold (3,564 sh), exited
  Constellation Brands, Alphabet add → Seeking Alpha, Yahoo Finance
- Viking SpaceX 1,200,000 sh → Benzinga
- Third Point Warner Bros. Discovery 20M sh / $533,200,000 → GuruFocus
- Tiger Global Cerebras $662,779,000 → Seeking Alpha
- TCI portfolio $52,769,884,406 → holdingschannel.com
- Fundsmith LLP 41 holdings / $13,648,923,682 → holdingschannel.com

## 3. Data-quality fixes applied 2026-08-17

- CUSIP→ticker overrides added (OpenFIGI "no match" on foreign-registered CUSIPs):
  G25457105 → CRDO (Credo), G7997R103 → STX (Seagate), N97284108 → NBIS (Nebius).
  All quarters regenerated; sectors reclassified.
- Every manager's top-10 main-book positions now have tickers.

## Known limitations

- 49 Q2 rows (small foreign ordinaries / warrants, none top-10) remain without tickers.
- Sector "Unclassified" bucket: 203 of 1,249 CUSIPs (mostly the same small foreign names).
- `data/ref/aum.csv` (Form ADV RAUM) not refreshed this cycle.
- Test suite: 36/36 passing (pytest, run 2026-08-17).
