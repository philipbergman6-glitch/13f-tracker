# 01 — Resolve all 20 manager names to SEC 13F filers (CIKs)

Type: research
Status: resolved
Blocked by: —

## Question

For each of the 20 names in the map's manager list, identify the SEC EDGAR filing
entity (or entities) behind it: exact filer name, CIK, most recent 13F-HR filing date
and period, and any complications (multiple related filers, combined filings, name
changes). Flag any name with **no** 13F filer (e.g., UK managers like Fundsmith and
Lindsell Train may file differently or not at all — verify, don't assume), and any
ambiguity (e.g., "Giverny" — Giverny Capital of Montreal vs other entities; "Leon
Cooperman" — Omega family offices post-conversion; "Icahn" — which Icahn entity files;
"Situational Awareness" — new fund, does it file yet?). Cite EDGAR URLs and retrieval
dates for everything. Note which managers have Q2-2026 filings in by the time of
research (deadline 2026-08-14).

## Answer

Resolved 2026-08-12. **All 20 names map to active SEC 13F filers — none are
"no-filer"** (both UK managers file: Fundsmith LLP CIK 1569205, Lindsell Train Ltd
CIK 1484150; TCI Fund Management Ltd CIK 1647251). Full table with CIKs, latest
filings, and source URLs: [notes/research/01-filer-resolution.md](../../../notes/research/01-filer-resolution.md).

Key findings:
- **Clean single filers (12):** Altimeter (1541617), Atreides (1777813), Coatue
  (1135730), Maverick (934639), Viking Global Investors (1103804), Third Point
  (1040273), Lone Pine (1061165), Tiger Global (1167483), Giverny Capital Inc.
  Montreal (1641864), TCI (1647251), Lindsell Train (1484150), Fairholme mgmt-co HR
  (1056831).
- **Filer successions (stitch history across CIKs):** Greenlight → DME Capital
  Management LP (1489933, from Q1-2024; combined filing incl. DME Advisors +
  Greenlight Masters); Appaloosa Management LP → Appaloosa LP (1656456, from
  Q1-2016); Omega Advisors → Cooperman Leon G individual (898382, from Q1-2019).
- **Combined/parent filings:** Berkshire Hathaway Inc (1067983, subsidiaries file
  13F-NT); Icahn = Carl C Icahn individual (921669, related entities file 13F-NT).
- **Two active filers per name (decide aggregate vs separate):** Pershing Square
  (PSCM LP 1336528 + Pershing Square Inc. 2026053 since Q2-2025); Fundsmith
  (LLP 1569205 + Fundsmith Investment Services Ltd 1868537); Situational Awareness
  (Situational Awareness LP 2045724, filing since Q4-2024, + Situational Awareness
  Partners LP 2038540, first HR Q1-2026 — relationship unverified).
- **Q2-2026 (period 2026-06-30) status as of 2026-08-12: 1/20 filed** — Lindsell
  Train only (filed 2026-07-15). The other 19 sit at Q1-2026; deadline is
  2026-08-14, so re-pull after the deadline.
