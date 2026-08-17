# Evidence package — 2026Q2 release

Generated 2026-08-17T17:12:09+00:00 from pipeline run 2026-08-17T17:12:06+00:00 (window 2024Q2–2026Q2, force_refresh=True), source commit `bbdf40efb4bf` with 8 uncommitted change(s) at generation time.

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
| 8 | Automated test results | `test_results.json` |
| 9 | Known exceptions and reviewer sign-off | `exceptions.csv + report.md` |
| 10 | SHA-256 checksums and source version | `checksums.csv + manifest.json` |

## 1. Filings used

201 filings across 2024Q2–2026Q2 (200 parsed 13F-HR/13F-HR/A, 1 13F-NT notice(s)). `filings.csv` lists, per filing: manager, filer CIK, form, accession, filing date, report period, SEC EDGAR URL, raw-data retrieval date, merge role, and cover-page reconciliation. Retrieval dates are the raw documents' download dates under `data/raw/` (immutable once fetched); 13F-NT retrieval dates are those of the SEC submissions index that evidences the notice.

### 2026Q2 filings (22)

| Manager | CIK | Form | Accession (EDGAR link) | Filed | Retrieved | Rows | Value ($) |
|---|---|---|---|---|---|---|---|
| Altimeter | 1541617 | 13F-HR | [0001541617-26-000008](https://www.sec.gov/Archives/edgar/data/1541617/000154161726000008/0001541617-26-000008-index.htm) | 2026-08-14 | 2026-08-17 | 20 | 9,829,676,383 |
| Appaloosa | 1656456 | 13F-HR | [0001656456-26-000003](https://www.sec.gov/Archives/edgar/data/1656456/000165645626000003/0001656456-26-000003-index.htm) | 2026-08-14 | 2026-08-17 | 27 | 7,725,383,349 |
| Atreides | 1777813 | 13F-HR | [0001777813-26-000009](https://www.sec.gov/Archives/edgar/data/1777813/000177781326000009/0001777813-26-000009-index.htm) | 2026-08-14 | 2026-08-17 | 49 | 14,335,417,162 |
| Berkshire Hathaway | 1067983 | 13F-HR | [0001193125-26-352200](https://www.sec.gov/Archives/edgar/data/1067983/000119312526352200/0001193125-26-352200-index.htm) | 2026-08-14 | 2026-08-17 | 89 | 299,253,556,246 |
| Coatue | 1135730 | 13F-HR | [0000919574-26-005478](https://www.sec.gov/Archives/edgar/data/1135730/000091957426005478/0000919574-26-005478-index.htm) | 2026-08-14 | 2026-08-17 | 211 | 48,629,053,706 |
| Fairholme | 1056831 | 13F-HR | [0000919574-26-005488](https://www.sec.gov/Archives/edgar/data/1056831/000091957426005488/0000919574-26-005488-index.htm) | 2026-08-14 | 2026-08-17 | 13 | 1,489,888,626 |
| Fundsmith | 1569205 | 13F-HR | [0001569205-26-000012](https://www.sec.gov/Archives/edgar/data/1569205/000156920526000012/0001569205-26-000012-index.htm) | 2026-08-14 | 2026-08-17 | 41 | 13,648,923,682 |
| Fundsmith | 1868537 | 13F-HR | [0001868537-26-000007](https://www.sec.gov/Archives/edgar/data/1868537/000186853726000007/0001868537-26-000007-index.htm) | 2026-08-14 | 2026-08-17 | 27 | 4,518,917,743 |
| Giverny | 1641864 | 13F-HR | [0001641864-26-000005](https://www.sec.gov/Archives/edgar/data/1641864/000164186426000005/0001641864-26-000005-index.htm) | 2026-08-14 | 2026-08-17 | 51 | 2,974,321,189 |
| Greenlight | 1489933 | 13F-HR | [0001172661-26-003786](https://www.sec.gov/Archives/edgar/data/1489933/000117266126003786/0001172661-26-003786-index.htm) | 2026-08-14 | 2026-08-17 | 95 | 3,908,853,490 |
| Icahn | 921669 | 13F-HR | [0001539497-26-002243](https://www.sec.gov/Archives/edgar/data/921669/000153949726002243/0001539497-26-002243-index.htm) | 2026-08-14 | 2026-08-17 | 18 | 8,264,090,525 |
| Leon Cooperman | 898382 | 13F-HR | [0000945621-26-001056](https://www.sec.gov/Archives/edgar/data/898382/000094562126001056/0000945621-26-001056-index.htm) | 2026-08-14 | 2026-08-17 | 39 | 3,547,427,123 |
| Lindsell Train | 1484150 | 13F-HR | [0001172661-26-002623](https://www.sec.gov/Archives/edgar/data/1484150/000117266126002623/0001172661-26-002623-index.htm) | 2026-07-15 | 2026-08-12 | 28 | 2,628,784,112 |
| Lone Pine | 1061165 | 13F-HR | [0000919574-26-005485](https://www.sec.gov/Archives/edgar/data/1061165/000091957426005485/0000919574-26-005485-index.htm) | 2026-08-14 | 2026-08-17 | 34 | 16,357,760,275 |
| Maverick Capital | 934639 | 13F-HR | [0000947871-26-000793](https://www.sec.gov/Archives/edgar/data/934639/000094787126000793/0000947871-26-000793-index.htm) | 2026-08-14 | 2026-08-17 | 179 | 11,320,923,736 |
| Pershing Square | 1336528 | 13F-NT | [0001172661-26-003777](https://www.sec.gov/Archives/edgar/data/1336528/000117266126003777/0001172661-26-003777-index.htm) | 2026-08-14 | 2026-08-17 | — | — |
| Pershing Square | 2026053 | 13F-HR | [0001172661-26-003790](https://www.sec.gov/Archives/edgar/data/2026053/000117266126003790/0001172661-26-003790-index.htm) | 2026-08-14 | 2026-08-17 | 15 | 19,465,692,772 |
| Situational Awareness | 2045724 | 13F-HR | [0000935836-26-000418](https://www.sec.gov/Archives/edgar/data/2045724/000093583626000418/0000935836-26-000418-index.htm) | 2026-08-14 | 2026-08-17 | 26 | 20,242,292,228 |
| TCI | 1647251 | 13F-HR | [0001647251-26-000007](https://www.sec.gov/Archives/edgar/data/1647251/000164725126000007/0001647251-26-000007-index.htm) | 2026-08-14 | 2026-08-17 | 11 | 52,769,884,406 |
| Third Point | 1040273 | 13F-HR | [0001040273-26-000003](https://www.sec.gov/Archives/edgar/data/1040273/000104027326000003/0001040273-26-000003-index.htm) | 2026-08-14 | 2026-08-17 | 43 | 4,679,571,988 |
| Tiger Global | 1167483 | 13F-HR | [0000919574-26-005427](https://www.sec.gov/Archives/edgar/data/1167483/000091957426005427/0000919574-26-005427-index.htm) | 2026-08-14 | 2026-08-17 | 46 | 23,981,506,027 |
| Viking Global | 1103804 | 13F-HR | [0001103804-26-000006](https://www.sec.gov/Archives/edgar/data/1103804/000110380426000006/0001103804-26-000006-index.htm) | 2026-08-14 | 2026-08-17 | 90 | 35,079,228,595 |

## 2. Parsed-vs-source reconciliation

For every parsed filing, the committed rows are reconciled against the filing's own cover page: parsed row count vs `tableEntryTotal` and summed `value_usd` vs `tableValueTotal`. Result: **199 of 200 filings match on rows and 197 of 200 on value totals**; every mismatch maps to a documented known exception:

| Filing | Rows parsed / declared | Value parsed / declared | Exception |
|---|---|---|---|
| Lindsell Train 2025Q1 `0001172661-25-001932` | 29 / 28 | 3,614,010,966 / 4,000,701,335 | EXC-001 |
| TCI 2025Q3 `0001647251-25-000014` | 9 / 9 | 52,699,548,226 / 52,699,548,227 | EXC-003 |
| Situational Awareness 2025Q4 `0002045724-26-000002` | 29 / 29 | 5,516,758,345 / 5,516,758,344 | EXC-002 |

## 3. Amendment-merge and duplicate decisions

`merge_decisions.csv` records, for each of the 201 decision rows, whether the filing is in its quarter-final book and why (quarter-final = latest RESTATEMENT, or the original 13F-HR, plus subsequent NEW HOLDINGS amendments — Form 13F Special Instruction 3). Decisions other than a lone original 13F-HR base:

| CIK | Quarter | Accession | Role | Why |
|---|---|---|---|---|
| 898382 | 2025Q1 | `0000945621-25-000492` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 898382 | 2025Q1 | `0000945621-25-000506` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 1067983 | 2025Q1 | `0000950123-25-008361` | NEW_HOLDINGS | NEW HOLDINGS amendment 1 appended after the base filing (Form 13F Special Instruction 3) |
| 1135730 | 2025Q4 | `0000919574-26-001239` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 1135730 | 2025Q4 | `0000919574-26-003414` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 1336528 | 2024Q4 | `0001172661-25-001497` | NEW_HOLDINGS | NEW HOLDINGS amendment 1 appended after the base filing (Form 13F Special Instruction 3) |
| 1641864 | 2024Q4 | `0001641864-25-000002` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 1641864 | 2024Q4 | `0001641864-25-000005` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 1641864 | 2025Q1 | `0001641864-25-000003` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 1641864 | 2025Q1 | `0001641864-25-000006` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 1641864 | 2025Q3 | `0001641864-25-000010` | SUPERSEDED_ORIGINAL | replaced by a later RESTATEMENT amendment |
| 1641864 | 2025Q3 | `0001641864-25-000011` | SUPERSEDED_RESTATEMENT | a later RESTATEMENT is the quarter-final base |
| 1641864 | 2025Q3 | `0001641864-25-000012` | BASE_RESTATEMENT | latest RESTATEMENT restates the quarter in its entirety |
| 2038540 | 2026Q1 | `0002038540-26-000004` | DUPLICATE_BOOK | Situational Awareness: book identical to filer 2045724 acc 0002045724-26-000008 (42 rows, CUSIP+class+put/call+type+shares+value multiset match); excluded to avoid double-counting Situational Awareness |

## 4. Multi-filer completeness

Every mapped (manager, filer, quarter) in the window has an explicit committed status (verified programmatically at package build): DUPLICATE=1, HOLDINGS=191, NT=1. None is LATE or ERROR (both block publication). Full table in `filer_status.csv`.

### 2026Q2 statuses

| Manager | Filer | CIK | Status | Detail |
|---|---|---|---|---|
| Altimeter | Altimeter Capital Management, LP | 1541617 | HOLDINGS | 20 rows from 1 filing(s) |
| Appaloosa | Appaloosa LP | 1656456 | HOLDINGS | 27 rows from 1 filing(s) |
| Atreides | Atreides Management, LP | 1777813 | HOLDINGS | 49 rows from 1 filing(s) |
| Berkshire Hathaway | BERKSHIRE HATHAWAY INC | 1067983 | HOLDINGS | 89 rows from 1 filing(s) |
| Coatue | COATUE MANAGEMENT LLC | 1135730 | HOLDINGS | 211 rows from 1 filing(s) |
| Fairholme | FAIRHOLME CAPITAL MANAGEMENT LLC | 1056831 | HOLDINGS | 13 rows from 1 filing(s) |
| Fundsmith | Fundsmith LLP | 1569205 | HOLDINGS | 41 rows from 1 filing(s) |
| Fundsmith | FUNDSMITH INVESTMENT SERVICES LTD. | 1868537 | HOLDINGS | 27 rows from 1 filing(s) |
| Giverny | Giverny Capital Inc. | 1641864 | HOLDINGS | 51 rows from 1 filing(s) |
| Greenlight | DME Capital Management, LP | 1489933 | HOLDINGS | 95 rows from 1 filing(s) |
| Icahn | ICAHN CARL C | 921669 | HOLDINGS | 18 rows from 1 filing(s) |
| Leon Cooperman | COOPERMAN LEON G | 898382 | HOLDINGS | 39 rows from 1 filing(s) |
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

0 errors, 42 warnings (`validation.csv`; errors block publication). Warning classes are calibrated against accepted SEC filings — see `notes/phase2-production-controls.md`.

## 6. Automated tests

`python -m unittest discover -s tests` (Python 3.14.6): **145 tests, PASS**, run 2026-08-17T17:12:07+00:00 (`test_results.json`). A failing suite blocks this package.

## 7. Known exceptions

Accepted filer-side discrepancies and scope decisions, from the committed register `data/ref/known_exceptions.csv` (each cites its source URL and retrieval date):

| ID | Quarter | Manager | Category | Summary | Resolution |
|---|---|---|---|---|---|
| EXC-001 | 2025Q1 | Lindsell Train | cover-page-mismatch | Cover page declares 28 table entries / $4,000,701,335; the filed info table contains 29 unique-CUSIP entries summing $3,614,010,966 | Filer-side cover-page error, never amended. The filed info table is the authoritative holdings list; the committed CSV matches it row-for-row and to the dollar |
| EXC-002 | 2025Q4 | Situational Awareness | cover-page-mismatch | Cover-page tableValueTotal is $1 below the info-table value sum | Filer-side rounding on the cover page. The filed info table is authoritative; the committed CSV matches it to the dollar |
| EXC-003 | 2025Q3 | TCI | cover-page-mismatch | Cover-page tableValueTotal is $1 above the info-table value sum | Filer-side rounding on the cover page. The filed info table is authoritative; the committed CSV matches it to the dollar |
| EXC-004 | 2024Q2 | Altimeter | cusip-cross-label | Altimeter's 2024Q2 filing swaps the issuer labels on CUSIPs 023135106 (Amazon) and 04626A103 (Astera Labs): 023135106 is labelled ASTERA LABS INC and 04626A103 AMAZON COM INC, the reverse of the CUSIPs' true issuers as filed by Maverick (acc 0000947871-24-000690) and all later quarters | Filer-side labelling error in the original filing, never amended. Committed CSVs faithfully reproduce the filed rows; the identity validation check (WARN) flags the disagreement each run. Ticker/sector joins key on CUSIP, so downstream aggregation is unaffected by the swapped labels |
| EXC-005 | 2026Q2 | Situational Awareness | scope-out | Situational Awareness Partners LP (CIK 2038540) filed no 13F-HR and no 13F-NT for 2026Q2; the Rule 13f-1 deadline was 2026-08-14. Its only 13F ever (2026Q1) was an exact duplicate of Situational Awareness LP's (CIK 2045724) book | Analyst decision (Philip, 2026-08-17): CIK 2038540 scoped to to_quarter=2026Q1 in manager_map.csv. Schedule 13G acc 0000935836-26-000303 names the LP as investment adviser to the Fund with jointly attributed positions, so the Adviser's 13F-HR carries the consolidated portfolio. Portfolio-coverage decision, not a legal conclusion; the CIK is monitored and an out-of-span 13F-HR from it fails the run |

## 8. Checksums and versions

`checksums.csv` holds SHA-256 digests for the release dashboard build and all 348 source data files it derives from (holdings CSVs, filer statuses, reference tables, change tables, run gate outputs). At publication, release.py re-verifies every digest against the artifacts being published. Source code version: commit `bbdf40efb4bf439f4a34c7a20512c66680d79850` (2026-08-17T19:56:40+03:00).

- `dashboard/staging/index.html` — SHA-256 `9023de90e406bd604155814de2ed1e9bda6ed95d97a572ef80c581d781b46aec`

## 9. How to reproduce this release

```
git checkout bbdf40efb4bf439f4a34c7a20512c66680d79850
python src/release.py stage --quarter 2026Q2 --start 2024Q2 --end 2026Q2
```

`stage` wraps, in order: `pipeline.py --force-refresh`, the full test suite, `dashboard.py --out dashboard/staging/index.html`, and this package's generation (add `--skip-figi` to reuse the committed ticker cache).

Raw EDGAR responses cache under `data/raw/` (re-fetchable; superseded mutable indexes are archived, not overwritten). Re-running against live EDGAR after the release date can differ only if a filer amends: compare the regenerated holdings CSVs against the digests in `checksums.csv` to detect any drift.

## Reviewer sign-off

Completed by a human reviewer before the release is considered approved: replace each blank below, commit this file, then run `python src/release.py publish --quarter 2026Q2`. The publish gate blocks unless the decision line begins with `approve` and the signed report is committed; regenerating this package rewrites the block blank, so a stale approval can never carry over.

- Reviewer name: ______________________
- Review date (YYYY-MM-DD): ______________________
- Decision (approve / reject, with notes): ______________________
