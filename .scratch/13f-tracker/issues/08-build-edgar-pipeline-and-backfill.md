# 08 — Build the EDGAR pull/parse pipeline and run the 8-quarter backfill

Type: task
Status: resolved (2026-08-12, AFK)
Assignee: claude (session 2026-08-12)
Blocked by: 03 (resolved)

## Question

Execution ticket (map carries execution). Build the pipeline per ticket 03's decisions:

- Committed manager→(CIK, quarter-range) mapping file from ticket 01's resolution
  (`notes/research/01-filer-resolution.md`), covering successions and multi-filer names.
- EDGAR fetch path per ticket 02: `data.sec.gov/submissions/CIK##########.json` →
  accessions → filing `index.json` → `primary_doc.xml` + infotable XML. Declared
  User-Agent, ≤10 req/s. Raw XML to gitignored `data\raw\`.
- Amendment merge to **quarter-final holdings** (RESTATEMENT replaces, NEW HOLDINGS
  adds) — first confirm the semantics against the SEC Form 13F instructions and note
  the citation; flag non-conforming amendment chains loudly.
- CUSIP→ticker via OpenFIGI with committed cache `data\ref\cusip_ticker.csv`
  (confirm free-tier terms first; manual-override column).
- Emit committed per-manager-quarter CSVs at `data\holdings\<manager>\<YYYYQn>.csv`
  with ticket 03's column set; changes tables (per the significant-change definition
  in CONTEXT.md) regenerate into `data\out\`.
- Run the 8-quarter backfill now; **re-pull after 2026-08-14** (Q2 deadline) as the
  live test of the late-filing/amendment path.

Resolution records: verification evidence (row counts vs `tableEntryTotal`, spot-check
against a live EDGAR filing and an eyeball Dataroma cross-check), OpenFIGI terms
citation, amendment-semantics citation, and any schema deviations discovered.

## Resolution (2026-08-12)

Built and backfilled. Pipeline in `src\` (`pipeline.py` entry point; `common.py`,
`edgar.py`, `build.py`, `figi.py`, `changes.py` — stdlib only, Python 3.14).
Re-runnable: raw EDGAR responses cached in `data\raw\`, OpenFIGI cache committed.

**Backfill result** (window 2024Q2–2026Q2, run 2026-08-12): 180 filings parsed
(13F-HR + 13F-HR/A) across 23 filer CIKs; 159 committed manager-quarter CSVs under
`data\holdings\<manager>\<YYYYQn>.csv` covering all 20 managers (8 quarters each;
Situational Awareness 6 — all that exist; 2026Q2 only Lindsell Train, as expected
pre-deadline); 139 change tables regenerated into `data\out\changes\`.

**Citations required by the ticket:**
- Amendment semantics: Form 13F **Special Instruction 3** (https://www.sec.gov/files/form13f.pdf,
  pp. 4–5, retrieved 2026-08-12): amendments "must either restate the Form 13F report in
  its entirety or include only holdings entries that are being reported in addition to
  those already reported in a current public Form 13F report for the same period" —
  RESTATEMENT replaces, NEW HOLDINGS adds, as coded in `src\build.py`.
- OpenFIGI terms: free and open to the public; unauthenticated = 25 requests/min,
  10 jobs/request (https://www.openfigi.com/api/documentation, retrieved 2026-08-12).
  Ran unauthenticated; no key stored.

**Verification evidence:**
- Row counts: 179/180 filings match their cover-page `tableEntryTotal`
  (`data\out\verification_rowcounts.csv`). The single mismatch is a **filer-side
  cover-page error**: Lindsell Train 13F-HR acc 0001172661-25-001932 (period
  2025-03-31) states 28 entries / $4,000,701,335 but its infotable contains 29 rows
  (Brown-Forman in two share classes) summing $3,614,010,966; no amendment was ever
  filed. Our CSV reflects the actual infotable.
- Amendment merge: Berkshire 2025Q1 = 110 rows from base 13F-HR (acc
  0000950123-25-005701) + exactly the 4 NEW HOLDINGS rows (D.R. Horton, Lennar ×2
  classes, Nucor) from 13F-HR/A acc 0000950123-25-008361 — matches ticket 02's live
  observation. Zero non-conforming amendment chains (`data\out\amendment_flags.csv`
  is empty).
- Live EDGAR spot-check: Pershing Square Capital Management 2026Q1 committed rows are
  an exact multiset match (cusip, issuer, value, shares) against a freshly re-fetched
  acc 0001172661-26-002336.
- Dataroma eyeball cross-check (manual QA per ADR 0001): dataroma.com/m/holdings.php?m=psc
  (retrieved 2026-08-12, period Q1 2026) shows 11 stocks / $13,714,300,000; BN
  59,697,208 sh / 17.62%; AMZN 11,451,981 sh / 17.39% — identical to our PSCM-only
  book ($13,714,299,861; weights match; their 11 vs our 10 is GOOG+GOOGL counted as
  two tickers for one issuer).

**Tickers:** 1,047/1,173 CUSIPs mapped (89%); 126 unmapped in
`data\ref\cusip_ticker.csv` with status (124 "no match" — mostly delisted/expired/
non-US instruments; 2 invalid-format CUSIPs, i.e. filer typos). Manual-override
column available; unmapped rows keep an empty ticker, never a guessed one.

**Schema deviations discovered:** none beyond the Lindsell Train cover-page error
above. Value column is whole dollars for the entire window (post-Jan-2023 rule).

**Still pending (by design):** re-pull after the 2026-08-14 Q2 deadline — spun out
as ticket 10 so it isn't lost.
