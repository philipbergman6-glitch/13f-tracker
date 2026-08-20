# Evidence package — 2026Q2 release

Generated 2026-08-20T08:40:03+00:00 from pipeline run 2026-08-20T08:36:36+00:00 (window 2024Q2–2026Q2, force_refresh=True), source commit `03489a230ab1` with 59 uncommitted change(s) at generation time.

Every figure below is copied from that run's outputs (nothing re-derived); machine-readable appendices sit next to this report. Required-item checklist:

| # | Required item | Where |
|---|---|---|
| 1 | SEC filing URLs and retrieval dates | `filings.csv` |
| 2 | CIK and accession numbers | `filings.csv` |
| 3 | Filing dates and report periods | `filings.csv` |
| 4 | Original row counts and cover-page totals | `filings.csv` |
| 5 | Parsed-vs-source reconciliation (rows and values) | `filings.csv` |
| 6 | Amendment-merge and duplicate decisions | `merge_decisions.csv` |
| 7 | Multi-filer completeness | `filer_status.csv` |
| 8 | Warning classifications and dispositions | `warning_dispositions.csv` |
| 9 | Automated test results | `test_results.json` |
| 10 | Known exceptions and reviewer sign-off | `exceptions.csv + report.md` |
| 11 | SHA-256 checksums and source version | `checksums.csv + manifest.json` |

## 1. Filings used

160 filings across 2024Q2–2026Q2 (159 parsed 13F-HR/13F-HR/A, 1 13F-NT notice(s)). `filings.csv` lists, per filing: manager, filer CIK, form, accession, filing date, report period, SEC EDGAR URL, raw-data retrieval date, merge role, and cover-page reconciliation. Retrieval dates are the raw documents' download dates under `data/raw/` (immutable once fetched); 13F-NT retrieval dates are those of the SEC submissions index that evidences the notice.

### 2026Q2 filings (18)

| Manager | CIK | Form | Accession (EDGAR link) | Filed | Retrieved | Rows | Value ($) |
|---|---|---|---|---|---|---|---|
| Altimeter | 1541617 | 13F-HR | [0001541617-26-000008](https://www.sec.gov/Archives/edgar/data/1541617/000154161726000008/0001541617-26-000008-index.htm) | 2026-08-14 | 2026-08-17 | 20 | 9,829,676,383 |
| Appaloosa | 1656456 | 13F-HR | [0001656456-26-000003](https://www.sec.gov/Archives/edgar/data/1656456/000165645626000003/0001656456-26-000003-index.htm) | 2026-08-14 | 2026-08-17 | 27 | 7,725,383,349 |
| Atreides | 1777813 | 13F-HR | [0001777813-26-000009](https://www.sec.gov/Archives/edgar/data/1777813/000177781326000009/0001777813-26-000009-index.htm) | 2026-08-14 | 2026-08-17 | 49 | 14,335,417,162 |
| Berkshire Hathaway | 1067983 | 13F-HR | [0001193125-26-352200](https://www.sec.gov/Archives/edgar/data/1067983/000119312526352200/0001193125-26-352200-index.htm) | 2026-08-14 | 2026-08-17 | 89 | 299,253,556,246 |
| Coatue | 1135730 | 13F-HR | [0000919574-26-005478](https://www.sec.gov/Archives/edgar/data/1135730/000091957426005478/0000919574-26-005478-index.htm) | 2026-08-14 | 2026-08-17 | 211 | 48,629,053,706 |
| Fundsmith | 1569205 | 13F-HR | [0001569205-26-000012](https://www.sec.gov/Archives/edgar/data/1569205/000156920526000012/0001569205-26-000012-index.htm) | 2026-08-14 | 2026-08-17 | 41 | 13,648,923,682 |
| Fundsmith | 1868537 | 13F-HR | [0001868537-26-000007](https://www.sec.gov/Archives/edgar/data/1868537/000186853726000007/0001868537-26-000007-index.htm) | 2026-08-14 | 2026-08-17 | 27 | 4,518,917,743 |
| Greenlight | 1489933 | 13F-HR | [0001172661-26-003786](https://www.sec.gov/Archives/edgar/data/1489933/000117266126003786/0001172661-26-003786-index.htm) | 2026-08-14 | 2026-08-17 | 95 | 3,908,853,490 |
| Lindsell Train | 1484150 | 13F-HR | [0001172661-26-002623](https://www.sec.gov/Archives/edgar/data/1484150/000117266126002623/0001172661-26-002623-index.htm) | 2026-07-15 | 2026-08-12 | 28 | 2,628,784,112 |
| Lone Pine | 1061165 | 13F-HR | [0000919574-26-005485](https://www.sec.gov/Archives/edgar/data/1061165/000091957426005485/0000919574-26-005485-index.htm) | 2026-08-14 | 2026-08-17 | 34 | 16,357,760,275 |
| Maverick Capital | 934639 | 13F-HR | [0000947871-26-000793](https://www.sec.gov/Archives/edgar/data/934639/000094787126000793/0000947871-26-000793-index.htm) | 2026-08-14 | 2026-08-17 | 179 | 11,320,923,736 |
| Pershing Square | 1336528 | 13F-NT | [0001172661-26-003777](https://www.sec.gov/Archives/edgar/data/1336528/000117266126003777/0001172661-26-003777-index.htm) | 2026-08-14 | 2026-08-20 | — | — |
| Pershing Square | 2026053 | 13F-HR | [0001172661-26-003790](https://www.sec.gov/Archives/edgar/data/2026053/000117266126003790/0001172661-26-003790-index.htm) | 2026-08-14 | 2026-08-17 | 15 | 19,465,692,772 |
| Situational Awareness | 2045724 | 13F-HR | [0000935836-26-000418](https://www.sec.gov/Archives/edgar/data/2045724/000093583626000418/0000935836-26-000418-index.htm) | 2026-08-14 | 2026-08-17 | 26 | 20,242,292,228 |
| TCI | 1647251 | 13F-HR | [0001647251-26-000007](https://www.sec.gov/Archives/edgar/data/1647251/000164725126000007/0001647251-26-000007-index.htm) | 2026-08-14 | 2026-08-17 | 11 | 52,769,884,406 |
| Third Point | 1040273 | 13F-HR | [0001040273-26-000003](https://www.sec.gov/Archives/edgar/data/1040273/000104027326000003/0001040273-26-000003-index.htm) | 2026-08-14 | 2026-08-17 | 43 | 4,679,571,988 |
| Tiger Global | 1167483 | 13F-HR | [0000919574-26-005427](https://www.sec.gov/Archives/edgar/data/1167483/000091957426005427/0000919574-26-005427-index.htm) | 2026-08-14 | 2026-08-17 | 46 | 23,981,506,027 |
| Viking Global | 1103804 | 13F-HR | [0001103804-26-000006](https://www.sec.gov/Archives/edgar/data/1103804/000110380426000006/0001103804-26-000006-index.htm) | 2026-08-14 | 2026-08-17 | 90 | 35,079,228,595 |

## 2. Parsed-vs-source reconciliation

For every parsed filing, the committed rows are reconciled against the filing's own cover page: parsed row count vs `tableEntryTotal` and summed `value_usd` vs `tableValueTotal`. Result: **158 of 159 filings match on rows and 156 of 159 on value totals**; every mismatch maps to a documented known exception:

| Filing | Rows parsed / declared | Value parsed / declared | Exception |
|---|---|---|---|
| Lindsell Train 2025Q1 `0001172661-25-001932` | 29 / 28 | 3,614,010,966 / 4,000,701,335 | EXC-001 |
| TCI 2025Q3 `0001647251-25-000014` | 9 / 9 | 52,699,548,226 / 52,699,548,227 | EXC-003 |
| Situational Awareness 2025Q4 `0002045724-26-000002` | 29 / 29 | 5,516,758,345 / 5,516,758,344 | EXC-002 |

## 3. Amendment-merge and duplicate decisions

`merge_decisions.csv` records, for each of the 160 decision rows, whether the filing is in its quarter-final book and why (quarter-final = latest RESTATEMENT, or the original 13F-HR, plus subsequent NEW HOLDINGS amendments — Form 13F Special Instruction 3). Decisions other than a lone original 13F-HR base:

| CIK | Quarter | Accession | Role | Why |
|---|---|---|---|---|
| 1067983 | 2025Q1 | `0000950123-25-008361` | NEW_HOLDINGS | NEW HOLDINGS amendment 1 appended after the base filing (Form 13F Special Instruction 3) |
| 1135730 | 2025Q4 | `0000919574-26-001239` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 1135730 | 2025Q4 | `0000919574-26-003414` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 1336528 | 2024Q4 | `0001172661-25-001497` | NEW_HOLDINGS | NEW HOLDINGS amendment 1 appended after the base filing (Form 13F Special Instruction 3) |
| 2038540 | 2026Q1 | `0002038540-26-000004` | DUPLICATE_BOOK | Situational Awareness: book identical to filer 2045724 acc 0002045724-26-000008 (42 rows, CUSIP+class+put/call+type+shares+value multiset match); excluded to avoid double-counting Situational Awareness |

## 4. Multi-filer completeness

Every mapped (manager, filer, quarter) in the window has an explicit committed status (verified programmatically at package build): DUPLICATE=1, HOLDINGS=155, NT=1. None is LATE or ERROR (both block publication). Full table in `filer_status.csv`.

### 2026Q2 statuses

| Manager | Filer | CIK | Status | Detail |
|---|---|---|---|---|
| Altimeter | Altimeter Capital Management, LP | 1541617 | HOLDINGS | 20 rows from 1 filing(s) |
| Appaloosa | Appaloosa LP | 1656456 | HOLDINGS | 27 rows from 1 filing(s) |
| Atreides | Atreides Management, LP | 1777813 | HOLDINGS | 49 rows from 1 filing(s) |
| Berkshire Hathaway | BERKSHIRE HATHAWAY INC | 1067983 | HOLDINGS | 89 rows from 1 filing(s) |
| Coatue | COATUE MANAGEMENT LLC | 1135730 | HOLDINGS | 211 rows from 1 filing(s) |
| Fundsmith | Fundsmith LLP | 1569205 | HOLDINGS | 41 rows from 1 filing(s) |
| Fundsmith | FUNDSMITH INVESTMENT SERVICES LTD. | 1868537 | HOLDINGS | 27 rows from 1 filing(s) |
| Greenlight | DME Capital Management, LP | 1489933 | HOLDINGS | 95 rows from 1 filing(s) |
| Lindsell Train | Lindsell Train Ltd | 1484150 | HOLDINGS | 28 rows from 1 filing(s) |
| Lone Pine | LONE PINE CAPITAL LLC | 1061165 | HOLDINGS | 34 rows from 1 filing(s) |
| Maverick Capital | MAVERICK CAPITAL LTD | 934639 | HOLDINGS | 179 rows from 1 filing(s) |
| Pershing Square | Pershing Square Capital Management, L.P. | 1336528 | NT | holdings reported in another filer's 13F (13F Notice) |
| Pershing Square | PERSHING SQUARE INC. | 2026053 | HOLDINGS | 15 rows from 1 filing(s) |
| Situational Awareness | Situational Awareness LP | 2045724 | HOLDINGS | 26 rows from 1 filing(s) |
| TCI | TCI Fund Management Ltd | 1647251 | HOLDINGS | 11 rows from 1 filing(s) |
| Third Point | Third Point LLC | 1040273 | HOLDINGS | 43 rows from 1 filing(s) |
| Tiger Global | TIGER GLOBAL MANAGEMENT LLC | 1167483 | HOLDINGS | 46 rows from 1 filing(s) |
| Viking Global | VIKING GLOBAL INVESTORS LP | 1103804 | HOLDINGS | 90 rows from 1 filing(s) |

## 5. Validation findings

0 errors, 36 warnings (`validation.csv`); **36 dispositioned and 0 unresolved**. Errors and any undispositioned warning block publication. `warning_dispositions.csv` records the classification, resolution, evidence reference, reviewer, and review date for every warning. Classification counts: confirmed-reported-trade=16, confirmed-warrant-movement=1, corporate-action=2, filer-identifier-anomaly=1, filer-label-error=2, filer-value-anomaly=1, issuer-label-variation=2, issuer-name-change=11.

## 6. Automated tests

`python -m unittest discover -s tests` (Python 3.14.6): **159 tests, PASS**, run 2026-08-20T08:40:02+00:00 (`test_results.json`). A failing suite blocks this package.

## 7. Known exceptions

Accepted filer-side discrepancies and scope decisions, from the committed register `data/ref/known_exceptions.csv` (each cites its source URL and retrieval date):

| ID | Quarter | Manager | Category | Summary | Resolution |
|---|---|---|---|---|---|
| EXC-001 | 2025Q1 | Lindsell Train | cover-page-mismatch | Cover page declares 28 table entries / $4,000,701,335; the filed info table contains 29 unique-CUSIP entries summing $3,614,010,966 | Filer-side cover-page error, never amended. The filed info table is the authoritative holdings list; the committed CSV matches it row-for-row and to the dollar |
| EXC-002 | 2025Q4 | Situational Awareness | cover-page-mismatch | Cover-page tableValueTotal is $1 below the info-table value sum | Filer-side rounding on the cover page. The filed info table is authoritative; the committed CSV matches it to the dollar |
| EXC-003 | 2025Q3 | TCI | cover-page-mismatch | Cover-page tableValueTotal is $1 above the info-table value sum | Filer-side rounding on the cover page. The filed info table is authoritative; the committed CSV matches it to the dollar |
| EXC-004 | 2024Q2 | Altimeter | cusip-cross-label | Altimeter's 2024Q2 filing swaps the issuer labels on CUSIPs 023135106 (Amazon) and 04626A103 (Astera Labs): 023135106 is labelled ASTERA LABS INC and 04626A103 AMAZON COM INC, the reverse of the CUSIPs' true issuers as filed by Maverick (acc 0000947871-24-000690) and all later quarters | Filer-side labelling error in the original filing, never amended. Committed CSVs faithfully reproduce the filed rows; the identity validation check (WARN) flags the disagreement each run. Ticker/sector joins key on CUSIP, so downstream aggregation is unaffected by the swapped labels |
| EXC-005 | 2026Q2 | Situational Awareness | scope-out | Situational Awareness Partners LP (CIK 2038540) filed no 13F-HR and no 13F-NT for 2026Q2; the Rule 13f-1 deadline was 2026-08-14. Its only 13F ever (2026Q1) was an exact duplicate of Situational Awareness LP's (CIK 2045724) book | Analyst decision (Philip, 2026-08-17): CIK 2038540 scoped to to_quarter=2026Q1 in manager_map.csv. Schedule 13G acc 0000935836-26-000303 names the LP as investment adviser to the Fund with jointly attributed positions, so the Adviser's 13F-HR carries the consolidated portfolio. Portfolio-coverage decision, not a legal conclusion; the CIK is monitored and an out-of-span 13F-HR from it fails the run |
| EXC-006 | 2025Q3 | Maverick Capital | filer-value-anomaly | Maverick reports Curis value $6,194 for 49,554 shares, implying $0.125 per share; an independent same-quarter accepted 13F reports a price near $2.32 | Preserve the original filed value and shares. Treat the quarter-over-quarter price warning as a documented filer-side value anomaly; do not normalize the immutable holdings row |

## 8. Checksums and versions

`checksums.csv` holds SHA-256 digests for the release dashboard build and all 316 source data files it derives from (holdings CSVs, filer statuses, reference tables, change tables, run gate outputs). At publication, release.py re-verifies every digest against the artifacts being published. Source code version: commit `03489a230ab13f60437586b363cb2cf0b2aad38d` (2026-08-17T21:58:34+03:00).

- `dashboard/staging/index.html` — SHA-256 `7ce80d2ae8e1f3a077041b5c115abe931822bbdf236c20483338cf10b98de4fa`

## 9. How to reproduce this release

```
git checkout 03489a230ab13f60437586b363cb2cf0b2aad38d
python src/release.py stage --quarter 2026Q2 --start 2024Q2 --end 2026Q2
```

`stage` wraps, in order: `pipeline.py --force-refresh`, the full test suite, `dashboard.py --out dashboard/staging/index.html`, and this package's generation (add `--skip-figi` to reuse the committed ticker cache).

Raw EDGAR responses cache under `data/raw/` (re-fetchable; superseded mutable indexes are archived, not overwritten). Re-running against live EDGAR after the release date can differ only if a filer amends: compare the regenerated holdings CSVs against the digests in `checksums.csv` to detect any drift.

## Reviewer sign-off

Completed by a human reviewer before the release is considered approved: replace each blank below, commit this file, then run `python src/release.py publish --quarter 2026Q2`. The publish gate blocks unless the decision line begins with `approve` and the signed report is committed; regenerating this package rewrites the block blank, so a stale approval can never carry over.

- Reviewer name: Philip
- Review date (YYYY-MM-DD): 2026-08-20
- Decision (approve / reject, with notes): approve — manager list trimmed to 16 (Icahn, Leon Cooperman, Fairholme, Giverny removed; holdings archived to data/_archive/holdings/)
