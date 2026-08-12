# Total-AUM estimate sources per manager (ticket 04)

Retrieved: 2026-08-12.

**Primary regulatory source used for most rows:** SEC Form ADV monthly compilation,
"Information About Registered Investment Advisers and Exempt Reporting Advisers",
file `ia08032026_0.zip` (registered advisers, data as of 2026-08-03), downloaded 2026-08-12 from
https://www.sec.gov/data-research/sec-markets-data/information-about-registered-investment-advisers-exempt-reporting-advisers
Field used: Item 5F(2)(c) — total regulatory assets under management (RAUM), plus "Latest ADV Filing Date".
RAUM per firm is verifiable interactively at `https://adviserinfo.sec.gov/firm/summary/<CRD>`.

Notes on what RAUM means: RAUM is gross regulatory AUM (includes leverage/uncalled
commitments in some structures) — usually >= net AUM the press quotes. It covers ALL the
adviser's clients worldwide, so it is a genuine total-AUM proxy, unlike 13F.

| # | Manager | Best source (URL) | AUM figure | As-of date | Confidence / notes |
|---|---------|-------------------|-----------:|------------|--------------------|
| 1 | Situational Awareness LP | Form ADV RAUM, CRD 333011 (https://adviserinfo.sec.gov/firm/summary/333011) | $9,278,344,000 | ADV filed 2026-06-11 | High (regulatory). Leopold Aschenbrenner's fund; young firm, RAUM moves fast — refresh from ADV amendments. |
| 2 | Altimeter Capital Management, LP | Form ADV RAUM, CRD 160017 (https://adviserinfo.sec.gov/firm/summary/160017) | $18,753,715,687 | ADV filed 2026-03-31 | High (regulatory). Includes private/venture vehicles not in 13F. |
| 3 | Atreides Management, LP | Form ADV RAUM, CRD 301152 (https://adviserinfo.sec.gov/firm/summary/301152) | $8,943,718,846 | ADV filed 2026-05-29 | High (regulatory). |
| 4 | Coatue Management, L.L.C. | Form ADV RAUM, CRD 157910 (https://adviserinfo.sec.gov/firm/summary/157910) | $92,705,722,582 | ADV filed 2026-07-29 | High (regulatory), very fresh. Large private book — expect big gap vs 13F. |
| 5 | Maverick Capital Ltd | Form ADV RAUM, CRD 108262 (https://adviserinfo.sec.gov/firm/summary/108262) | $15,846,499,306 | ADV filed 2026-03-31 | High (regulatory). RAUM is gross (long+short leverage); net AUM lower. |
| 6 | Viking Global Investors LP | Form ADV RAUM, CRD 132272 (https://adviserinfo.sec.gov/firm/summary/132272) | $78,202,235,935 | ADV filed 2026-06-15 | High (regulatory). Gross RAUM; Viking's stated net AUM in press is ~half. |
| 7 | Greenlight (Einhorn) — DME Capital Management, LP | Form ADV RAUM, CRD 157081 (https://adviserinfo.sec.gov/firm/summary/157081) | $4,798,925,830 | ADV filed 2026-05-01 | High (regulatory). Greenlight Capital's management co. registers as DME Capital Management. Related registrants: DME Advisors LP (reinsurance sidecar, CRD 157074, $906,973,741) and Greenlight Masters LLC (fund-of-funds, CRD 157082, $1,267,719,953) — do not sum blindly, possible overlap. |
| 8 | Icahn (Icahn Enterprises / Icahn Capital) | IEP Q2 2026 results 8-K exhibit (https://www.sec.gov/Archives/edgar/data/813762/000110465926090743/tm2622273d1_ex99-1.htm) | Indicative NAV ≈ $2.6bn (press release: decrease of $765m vs 2026-03-31) | 2026-06-30 (release dated 2026-08-05) | High for what it is, but structurally different: Icahn Capital deregistered from ADV (family capital only). Indicative NAV is IEP holding-company value, not a manager AUM. IEP total assets (10-Q) are much larger but include operating subsidiaries. No ADV RAUM exists. |
| 9 | Fairholme Capital Management, L.L.C. | Form ADV RAUM, CRD 107987 (https://adviserinfo.sec.gov/firm/summary/107987) | $2,141,157,171 | ADV filed 2026-03-27 | High (regulatory). |
| 10 | Pershing Square Capital Management, L.P. | Form ADV RAUM, CRD 132982 (https://adviserinfo.sec.gov/firm/summary/132982) | $25,061,606,673 | ADV filed 2026-06-03 | High (regulatory). Cross-check available weekly: Pershing Square Holdings publishes NAV at https://pershingsquareholdings.com (PSH is a subset of firm AUM). |
| 11 | Third Point LLC | Form ADV RAUM, CRD 137927 (https://adviserinfo.sec.gov/firm/summary/137927) | $28,732,008,681 | ADV filed 2026-05-01 | High (regulatory). Includes assets managed for Third Point Re/Malibu Life reinsurance; hedge-fund AUM quoted in press is smaller. TPIL (LSE-listed) NAV also published monthly. |
| 12 | Berkshire Hathaway | 10-Q via SEC EDGAR XBRL API (https://data.sec.gov/api/xbrl/companyconcept/CIK0001067983/us-gaap/EquitySecuritiesFvNi.json) | Equity securities at fair value $323,779,000,000; total shareholders' equity $747,910,000,000 | 2026-06-30 (10-Q filed 2026-08-10) | High (regulatory filing). Operating company — no AUM concept. For a 13F-vs-total comparison use equity-securities fair value ($323.8bn); shareholders' equity is the broader capital base. Note 13F misses foreign-listed holdings (e.g. Japan trading houses). |
| 13 | Lone Pine Capital LLC | Form ADV RAUM, CRD 156602 (https://adviserinfo.sec.gov/firm/summary/156602) | $21,624,342,800 | ADV filed 2026-03-30 | High (regulatory). Gross RAUM. |
| 14 | Appaloosa LP | Form ADV RAUM, CRD 281909 (https://adviserinfo.sec.gov/firm/summary/281909) | $20,396,101,407 | ADV filed 2026-03-25 | High (regulatory). Effectively a family office (Tepper) but still SEC-registered, so RAUM exists. |
| 15 | Tiger Global Management, LLC | Form ADV RAUM, CRD 160318 (https://adviserinfo.sec.gov/firm/summary/160318) | $77,993,959,953 | ADV filed 2026-03-27 | High (regulatory). Dominated by private/venture funds; 13F covers only the public book. |
| 16 | Giverny Capital | Form ADV RAUM — two candidate entities: Giverny Capital Inc. (Rochon, Montreal), CRD 130640 (https://adviserinfo.sec.gov/firm/summary/130640): $2,703,277,172, ADV filed 2026-06-12; Giverny Capital Asset Management LLC (Poppe, NY), CRD 306473 (https://adviserinfo.sec.gov/firm/summary/306473): $599,391,058, ADV filed 2026-03-30 | see source column | 2026-06-12 / 2026-03-30 | High (regulatory) once entity is pinned. AMBIGUITY: two affiliated firms file separate 13Fs — confirm which CIK the dashboard tracks before choosing the RAUM row. |
| 17 | Leon Cooperman (Omega Family Office) | No regulatory source — Omega Advisors deregistered end-2018 (CNBC, 2018-07-23: https://www.cnbc.com/2018/07/23/coopermans-omega-is-converting-to-family-office.html) | No public figure | — | Family office; no ADV, no firm-published AUM. Bio-page claims of ">$10bn" (e.g. https://www.csis.org/people/leon-cooperman, retrieved 2026-08-12) are undated and unverified — do not use as data. Fallback: 13F long value only, labelled as such. |
| 18 | TCI Fund Management Ltd | Press: Forbes, 2026-01-18 (https://www.forbes.com/sites/hanktucker/2026/01/18/hedge-fund-billionaire-chris-hohns-tci-profited-by-a-record-189-billion-in-2025/), retrieved 2026-08-12 | $77.1bn (hedge-fund assets; figure originates from LCH Investments annual survey) | end-2025 | Medium (press-only, single source; second independent source needed before decision use). UK manager; SEC status is exempt reporting adviser (CRD 269954) — ERAs do not report RAUM. FCA/Companies House accounts are the regulatory fallback (not fetched today). |
| 19 | Fundsmith | Form ADV RAUM — two registrants: Fundsmith LLP (UK), CRD 160365 (https://adviserinfo.sec.gov/firm/summary/160365): $18,508,143,977, ADV filed 2026-06-26; Fundsmith Investment Services Ltd, CRD 310498 (https://adviserinfo.sec.gov/firm/summary/310498): $24,575,319,221, ADV filed 2026-06-29 | see source column | 2026-06-26 / 2026-06-29 | Medium-high. Both entities are SEC-registered with RAUM, but the split/overlap between them is unclear — do NOT sum without checking ADV Item 5. Firm-wide figure also published in Fundsmith Equity Fund factsheets (fundsmith.co.uk blocks automated fetch; check manually). |
| 20 | Lindsell Train Limited | Form ADV RAUM, CRD 158323 (https://adviserinfo.sec.gov/firm/summary/158323) | $9,254,180,434 | ADV filed 2026-04-27 | High (regulatory). UK manager but SEC-registered, so RAUM covers the firm. Monthly fund-level FUM in factsheets at lindselltrain.com (homepage carries no firm total — checked 2026-08-12). |

## Refresh recipe (for the dashboard)

- RAUM rows: re-download the latest monthly zip from the SEC page above (new file ~monthly,
  named `iaMMDDYYYY.zip`), key on CRD, read column `5F(2)(c)` and `Latest ADV Filing Date`.
  Advisers must amend ADV annually (within 90 days of fiscal year-end), so most RAUM figures
  update Feb–Apr.
- Berkshire: EDGAR XBRL companyconcept API, tags `EquitySecuritiesFvNi` and
  `StockholdersEquity`, CIK 0001067983 — quarterly.
- Icahn: IEP quarterly earnings 8-K, "Indicative Net Asset Value" — quarterly.
- TCI: no regulatory RAUM; re-check press each January (LCH Investments survey season) or
  pull FCA/Companies House annual accounts.
- Cooperman: no public figure; display 13F long value only, labelled.

## Caveats (observed vs inferred)

- All RAUM figures above were read directly from the SEC compilation file dated 2026-08-03
  (observed). The claim that DME Capital Management = Greenlight's management company is
  inferred from the shared filer family (DME Advisors / Greenlight Masters share address and
  CRD block) — verify against Greenlight's 13F filer name before wiring it in.
- RAUM vs net AUM: for levered long/short funds (Maverick, Viking, Lone Pine) RAUM can be
  roughly 1.5–2x net AUM. This is a structural point (inferred, standard ADV mechanics), so
  label the dashboard column "regulatory AUM (gross)" not "AUM".
