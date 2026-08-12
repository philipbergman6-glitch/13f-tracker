# 13F filer resolution — 20 managers

Ticket: `.scratch/13f-tracker/issues/01-resolve-managers-to-sec-filers.md`
Retrieved: **2026-08-12** (all rows). Method: EDGAR company search
(`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=<name>&type=13F&owner=include&count=100`)
to enumerate candidate CIKs, then live `https://data.sec.gov/submissions/CIK##########.json`
per CIK for authoritative filer name, former names, address, and 13F filing history.
Requests sent with User-Agent "GEMS Investment Research gemsai62@gmail.com" per SEC fair-use policy.

Q2-2026 = period 2026-06-30; filing deadline 2026-08-14. As of retrieval, **1 of 20**
(Lindsell Train) has a Q2-2026 13F-HR on file; the other 19 filers' latest period is
2026-03-31 (Q1-2026), all filed 2026-05-15 to 2026-05-18.

| Given name | Filer name (EDGAR) | CIK | Latest 13F-HR filed | Period | Q2-2026 filed? | Notes / flags | Source URL |
|---|---|---|---|---|---|---|---|
| Situational Awareness | Situational Awareness LP | 2045724 | 2026-05-18 | 2026-03-31 | No | Aschenbrenner's fund does file; first 13F-HR 2025-02-12 (period 2024-12-31). SF, CA. **Second SF entity "Situational Awareness Partners LP" (CIK 2038540)** filed its own first 13F-HR 2026-05-18 (period 2026-03-31) — relationship between the two entities unverified; track both. | https://data.sec.gov/submissions/CIK0002045724.json ; https://data.sec.gov/submissions/CIK0002038540.json |
| Altimeter Capital Management | Altimeter Capital Management, LP | 1541617 | 2026-05-15 | 2026-03-31 | No | Former name: Altimeter Capital Management, LLC. Clean single filer. | https://data.sec.gov/submissions/CIK0001541617.json |
| Atreides Management | Atreides Management, LP | 1777813 | 2026-05-18 | 2026-03-31 | No | Clean single filer. | https://data.sec.gov/submissions/CIK0001777813.json |
| Coatue Management | COATUE MANAGEMENT LLC | 1135730 | 2026-05-15 | 2026-03-31 | No | Clean; note 13F-HR/A for 2025-12-31 filed 2026-05-15 (amendments common). | https://data.sec.gov/submissions/CIK0001135730.json |
| Maverick Capital | MAVERICK CAPITAL LTD | 934639 | 2026-05-15 | 2026-03-31 | No | Second CIK 928617 "MAVERICK CAPITAL LTD /ADV" is historical (last 13F 2002). | https://data.sec.gov/submissions/CIK0000934639.json |
| Viking Global | VIKING GLOBAL INVESTORS LP | 1103804 | 2026-05-15 | 2026-03-31 | No | CIK 1101785 "Viking Global Equities LP" is historical (last 13F 2002). | https://data.sec.gov/submissions/CIK0001103804.json |
| Greenlight (David Einhorn) | DME Capital Management, LP | 1489933 | 2026-05-15 | 2026-03-31 | No | **Filer changed.** GREENLIGHT CAPITAL INC (CIK 1079114) stopped after period 2023-12-31 (filed 2024-02-14). Current combined 13F-HR by DME Capital Management, LP includes DME Advisors, LP (CIK 1300763, former name Greenlight Capital Advisors, L.L.C. — files 13F-NT) and Greenlight Masters, LLC (CIK 1449674) — verified from cover page of acc 0001172661-26-002341 (signed Daniel Roitman, COO). | https://data.sec.gov/submissions/CIK0001489933.json ; https://www.sec.gov/Archives/edgar/data/1489933/000117266126002341/primary_doc.xml |
| Icahn | ICAHN CARL C | 921669 | 2026-05-15 | 2026-03-31 | No | Combined filing by the individual (former conformed name "ICAHN CARL C ET AL"). ICAHN CAPITAL LP (CIK 1412093) files 13F-NT (latest 2026-05-15); ICAHN ENTERPRISES HOLDINGS L.P. (CIK 1034563) filed 13F-NTs through period 2025-09-30 (latest 2025-11-14). Several other Icahn CIKs are historical (Icahn & Co Inc 881188, Icahn Institutional Services 1164756, etc.). | https://data.sec.gov/submissions/CIK0000921669.json |
| Fairholme | FAIRHOLME CAPITAL MANAGEMENT LLC | 1056831 | 2026-05-15 | 2026-03-31 | No | FAIRHOLME FUNDS INC (CIK 1096344) files 13F-NT alongside; older Fairholme entities historical. | https://data.sec.gov/submissions/CIK0001056831.json |
| Pershing Square | Pershing Square Capital Management, L.P. | 1336528 | 2026-05-15 | 2026-03-31 | No | **Second active filer:** PERSHING SQUARE INC. (CIK 2026053, former name Pershing Square Holdco, L.P.) has filed its own 13F-HR since period 2025-06-30 — track both if full coverage wanted. Old GP entities (1336476, 1336483, 1336481) historical 13F-NT only. | https://data.sec.gov/submissions/CIK0001336528.json ; https://data.sec.gov/submissions/CIK0002026053.json |
| Third Point | Third Point LLC | 1040273 | 2026-05-15 | 2026-03-31 | No | Former name: THIRD POINT MANAGEMENT CO LLC. Clean single filer. | https://data.sec.gov/submissions/CIK0001040273.json |
| Berkshire Hathaway | BERKSHIRE HATHAWAY INC | 1067983 | 2026-05-15 | 2026-03-31 | No | Parent files combined 13F-HR; insurance subsidiaries (e.g. BH Homestate Insurance CIK 829771, BH Life Insurance of Nebraska CIK 1015867) file 13F-NT covered by parent. History of confidential-treatment 13F-HR/A amendments (e.g. 2025-08-14 amendment for period 2025-03-31). OBH LLC (CIK 109694) is a historical former-name entity. | https://data.sec.gov/submissions/CIK0001067983.json |
| Lone Pine | LONE PINE CAPITAL LLC | 1061165 | 2026-05-15 | 2026-03-31 | No | Clean single filer. | https://data.sec.gov/submissions/CIK0001061165.json |
| Appaloosa | Appaloosa LP | 1656456 | 2026-05-15 | 2026-03-31 | No | **Filer changed:** APPALOOSA MANAGEMENT LP (CIK 1006438) stopped after period 2015-12-31; Appaloosa LP (Short Hills, NJ — Tepper) is the current filer. | https://data.sec.gov/submissions/CIK0001656456.json |
| Tiger Global | TIGER GLOBAL MANAGEMENT LLC | 1167483 | 2026-05-15 | 2026-03-31 | No | Former names: Tiger Technology Management (LLC). Clean single filer. | https://data.sec.gov/submissions/CIK0001167483.json |
| Giverny | Giverny Capital Inc. | 1641864 | 2026-05-15 | 2026-03-31 | No | Montreal, Quebec entity confirmed (the intended one). Two US affiliates — Giverny Capital Advisors LLC (CIK 2034934, Skillman NJ) and Giverny Capital Asset Management, LLC (CIK 2035712, NYC) — each filed a single 13F-NT in Aug 2024, nothing since; unverified whether their holdings roll into another manager's HR. Last year's Q2 HR came 2025-08-13, so Q2-2026 likely imminent. | https://data.sec.gov/submissions/CIK0001641864.json |
| Leon Cooperman | COOPERMAN LEON G | 898382 | 2026-05-15 | 2026-03-31 | No | Files as an individual post family-office conversion. Omega Advisors Inc. (CIK 898202) stopped after period 2018-12-31 (filed 2019-02-14). | https://data.sec.gov/submissions/CIK0000898382.json |
| TCI | TCI Fund Management Ltd | 1647251 | 2026-05-15 | 2026-03-31 | No | London-based but files 13F (Section 13(f) applies to any manager using US-jurisdiction means). Company search for "Children's Investment" finds nothing — search "TCI Fund". | https://data.sec.gov/submissions/CIK0001647251.json |
| Fundsmith | Fundsmith LLP | 1569205 | 2026-05-15 | 2026-03-31 | No | UK manager **does** file. **Second active filer:** FUNDSMITH INVESTMENT SERVICES LTD. (CIK 1868537, Mauritius) files its own 13F-HR (latest 2026-05-15, period 2026-03-31). Historical: Fundsmith Equity Fund, L.P. (1520023, last 2018) and Fundsmith Long/Short Master Fund (1813932, last 2021). | https://data.sec.gov/submissions/CIK0001569205.json ; https://data.sec.gov/submissions/CIK0001868537.json |
| Lindsell Train | Lindsell Train Ltd | 1484150 | 2026-07-15 | **2026-06-30** | **Yes** | UK manager **does** file, and is the only one of the 20 with Q2-2026 already in (filed 2026-07-15, a month ahead of deadline — habitual early filer). | https://data.sec.gov/submissions/CIK0001484150.json |

## Notes

- **Q2-2026 status (as of 2026-08-12):** 1/20 filed (Lindsell Train). Deadline is
  2026-08-14, and most of these filers historically file on the deadline day, so
  expect the bulk on 2026-08-13/14. Re-check after the deadline.
- **Filer successions to encode in the tracker:** Greenlight → DME Capital Management LP
  (from Q1-2024); Appaloosa Management LP → Appaloosa LP (from Q1-2016); Omega Advisors →
  Cooperman Leon G (from Q1-2019). Stitch histories across these CIK pairs if building
  long time series.
- **Combined/multi-filer structures:** Berkshire (parent HR + subsidiary NTs), Icahn
  (Carl C Icahn HR + Icahn Capital LP / Icahn Enterprises Holdings NTs), Greenlight/DME
  (DME Capital Management HR includes DME Advisors + Greenlight Masters), Fairholme
  (management-company HR + Fairholme Funds NT). For holdings, the 13F-HR filer is the
  one to pull; NT filers carry no holdings.
- **Two genuinely separate active filers:** Pershing Square (PSCM LP + Pershing Square
  Inc., since Q2-2025) and Fundsmith (Fundsmith LLP + Fundsmith Investment Services
  Ltd.); Situational Awareness likewise has two LPs as of Q1-2026 — decide whether to
  aggregate or track separately.
- **Ambiguities resolved:** "Giverny" = Giverny Capital Inc., Montreal (address verified
  in submissions JSON); "Icahn" HR filer = the individual Carl C. Icahn, CIK 921669;
  "Leon Cooperman" = individual CIK 898382; "Situational Awareness" does file
  (since period 2024-12-31).
- **Unverified items (flagged, not assumed):** the relationship between Situational
  Awareness LP and Situational Awareness Partners LP; whether the two 2024-only Giverny
  US affiliates' holdings are reported under another manager's HR.
- All facts above observed directly in the cited EDGAR/data.sec.gov responses on
  2026-08-12; nothing stated from memory.
