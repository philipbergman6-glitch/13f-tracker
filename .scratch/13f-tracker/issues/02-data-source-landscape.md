# 02 — Data-source landscape: EDGAR vs Dataroma vs WhaleWisdom

Type: research
Status: resolved
Blocked by: —

## Question

Gather the facts needed to choose the pipeline's source of truth (decision itself is
ticket 03):

- **SEC EDGAR**: how 13F-HR data is exposed (info-table XML format, full-text search,
  the `data.sec.gov` JSON APIs, bulk download options), rate limits / fair-use rules,
  User-Agent requirements, and how amendments (13F-HR/A) appear. Feasibility of pulling
  8 quarters × 20 managers.
- **Dataroma**: which of our 16 dataroma-listed managers it actually covers, what it
  adds beyond EDGAR (activity classification, history depth), page structure, and its
  terms of use / robots.txt stance on automated access.
- **WhaleWisdom**: coverage of the 4 WhaleWisdom-only names, free vs paid tiers, API
  availability, terms of use.

Cite URLs + retrieval dates. Output should let ticket 03 be decided in one conversation.

## Answer

Full findings (every fact cited with URL + retrieval date 2026-08-12):
`notes/research/02-data-source-landscape.md`.

Summary:

- **EDGAR**: each 13F = `primary_doc.xml` (cover page incl. `amendmentType`) + a
  filer-named infotable XML (schema verified on a live Berkshire filing). Pipeline path:
  `data.sec.gov/submissions/CIK##########.json` → accession → filing `index.json` → two
  XMLs. No 13F frankenquery on data.sec.gov (submissions + XBRL APIs only). Full-text
  search API (`efts.sec.gov/LATEST/search-index`) tested and works. Bulk: daily/quarterly
  indexes (1994Q3+) and DERA quarterly TSV zips (2013Q2+, ~99 MB/qtr compressed, 7 tables
  incl. INFOTABLE + COVERPAGE with ISAMENDMENT/AMENDMENTTYPE). Fair use: 10 req/s max,
  declared User-Agent required (undeclared UA got 403 in testing). 8 qtrs × 20 managers ≈
  ~400 small requests ≈ minutes — trivially feasible. Amendments: separate 13F-HR/A
  filings; `amendmentType` = RESTATEMENT (replaces table) or NEW HOLDINGS (adds; observed
  live). Caveat: Situational Awareness has only 6 quarters of filings (first 2025-02-12).
- **Dataroma**: covers all 16 target managers (codes captured in findings). Adds
  buy/sell/add/reduce classification and 13+ years of activity history; clean
  server-rendered HTML. No robots.txt (302 to home), TOS silent on scraping but forbids
  republishing/reproducing its content beyond small cited excerpts.
- **WhaleWisdom**: covers all 4 WhaleWisdom-only names (Altimeter under
  `altimeter-partners-fund-lp`; management-entity slug needs one-time disambiguation).
  Scraping prohibited by TOU and robots.txt. Keyed API exists: free tier = trailing 8
  quarters excluding current quarter, 20 req/min; current-quarter API access from
  $90/quarter (Standard); Enterprise = unlimited API + nightly FTP.
- Provenance: EDGAR is the primary source both aggregators ingest, unrestricted and free;
  aggregator content is redistribution-restricted. Decision itself is ticket 03.
