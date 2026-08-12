# 02 — Data-source landscape: EDGAR vs Dataroma vs WhaleWisdom

Research for ticket `.scratch/13f-tracker/issues/02-data-source-landscape.md`.
All facts retrieved **2026-08-12** unless noted. Method: direct HTTP fetches with a
declared User-Agent ("GEMS Investment Research gemsai62@gmail.com" for SEC hosts, a
browser UA for the two commercial sites — read-only page loads, no login, no accounts
created). Anything not directly observed is marked **[inferred]** or **[unverified]**.

---

## A) SEC EDGAR (primary candidate)

### A.1 How a 13F filing is structured on EDGAR (observed on a live filing)

Each 13F submission is a folder under
`https://www.sec.gov/Archives/edgar/data/{CIK}/{accession-no-dashes}/` containing two
small XML files plus index wrappers. Observed on Berkshire Hathaway 13F-HR/A, accession
0000950123-25-008361 (https://www.sec.gov/Archives/edgar/data/1067983/000095012325008361/index.json,
retrieved 2026-08-12):

- `primary_doc.xml` (2,854 bytes) — the cover page: `reportCalendarOrQuarter`,
  `isAmendment`, `amendmentNo`, `amendmentType`, `reportType`, `tableEntryTotal`,
  `tableValueTotal`, `isConfidentialOmitted`, signature block.
- `43981.xml` (2,134 bytes) — the **information table**, root element
  `<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">`,
  one `<infoTable>` per row with: `nameOfIssuer`, `titleOfClass`, `cusip`, `value`
  (USD), `shrsOrPrnAmt/sshPrnamt` + `sshPrnamtType` (SH/PRN), `investmentDiscretion`,
  `otherManager`, `votingAuthority/{Sole,Shared,None}`
  (https://www.sec.gov/Archives/edgar/data/1067983/000095012325008361/43981.xml,
  retrieved 2026-08-12). The infotable filename is filer-chosen (here `43981.xml`),
  so a parser must locate it via the filing's `index.json` rather than a fixed name.
- Every filing directory is browsable as `index.html` / `index.xml` / `index.json`
  (SEC "Accessing EDGAR Data",
  https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data,
  retrieved 2026-08-12 — `https://www.sec.gov/os/accessing-edgar-data` 302-redirects there).

The XML schema is formally defined in the EDGAR Form 13F XML Technical Specification
(taxonomy of .xsd files); spec collection at https://www.sec.gov/info/edgar/tech-specs,
current draft v1.6 page:
https://www.sec.gov/edgar/filer-information/specifications/form13fxmltechspec-draft
(located via web search 2026-08-12; spec PDF content not read — schema above was
verified against a live filing instead).

### A.2 data.sec.gov JSON APIs

Documented at
https://www.sec.gov/search-filings/edgar-application-programming-interfaces
(retrieved 2026-08-12). Endpoints listed there:

- `https://data.sec.gov/submissions/CIK##########.json` — full filing history per CIK.
  **Tested live** for Berkshire (CIK 0001067983): returns filer name plus parallel
  arrays `form`, `filingDate`, `accessionNumber`, `primaryDocument`; contained 43
  13F-HR/13F-HR/A rows in the `recent` block, with older history paged out to
  `CIK0001067983-submissions-001.json` (1,390 filings back to 1998-08-10)
  (https://data.sec.gov/submissions/CIK0001067983.json, retrieved 2026-08-12).
- XBRL APIs: `api/xbrl/companyconcept`, `api/xbrl/companyfacts`, `api/xbrl/frames`,
  plus bulk `submissions.zip` and `companyfacts.zip`.
- **No 13F-holdings "frankenquery" exists on data.sec.gov**: the documented API set is
  submissions + XBRL only; 13F information tables are not XBRL, so the frames/facts
  APIs do not expose them (observed from the API doc page above; the absence is as
  documented — no hidden endpoint was searched for beyond the official docs).

So the API-based pipeline shape is: submissions JSON → accession numbers of 13F-HR /
13F-HR/A → filing `index.json` → fetch `primary_doc.xml` + infotable XML.

### A.3 EDGAR full-text search API

- UI: https://efts.sec.gov backend, endpoint
  `https://efts.sec.gov/LATEST/search-index?q=...&forms=13F-HR`.
  **Tested live**: `q="Maverick Capital"&forms=13F-HR` returned JSON with
  `hits.total.value = 116`, first hit `MAVERICK CAPITAL LTD (CIK 0000934639)`,
  file_type 13F-HR (retrieved 2026-08-12). Useful for CIK discovery, not needed for
  the holdings pull itself.
- Filer-name → CIK lookup also works via the classic company browse endpoint,
  e.g. `https://www.sec.gov/cgi-bin/browse-edgar?company=situational+awareness&type=13F&action=getcompany&output=atom`
  (**tested live** 2026-08-12; returned CIKs 0002045724 and 0002038540).

### A.4 Bulk options

1. **Daily/quarterly index files** — `/Archives/edgar/daily-index` and
   `/Archives/edgar/full-index` (form/company/master/XBRL indexes, 1994Q3–present;
   full+quarterly indexes rebuilt weekly early Saturday so post-acceptance corrections
   get incorporated). Source: SEC "Accessing EDGAR Data" page (URL in A.1, retrieved
   2026-08-12).
2. **DERA structured Form 13F data sets** —
   https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
   (`https://www.sec.gov/dera/data/form-13f` 302-redirects there; retrieved 2026-08-12):
   - Quarterly zips from 2013 Q2 onward; since March 2024 the periods run
     Mar–May / Jun–Aug / Sep–Nov / Dec–Feb, "publication is intended to follow closely
     after the 13F due dates". Latest listed: `01mar2026-31may2026_form13f.zip`.
   - Data is "as-filed", flattened, extracted from the XML portion of submissions;
     SEC's own disclaimer says it is not a substitute for the filings.
   - **Tested live**: downloaded `01mar2026-31may2026_form13f.zip`
     (https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01mar2026-31may2026_form13f.zip,
     99,411,274 bytes compressed, retrieved 2026-08-12). Contents: `COVERPAGE.tsv`,
     `INFOTABLE.tsv` (396 MB uncompressed for one quarter — all ~8,000+ filers, not
     just ours), `OTHERMANAGER.tsv`, `OTHERMANAGER2.tsv`, `SIGNATURE.tsv`,
     `SUBMISSION.tsv`, `SUMMARYPAGE.tsv`, metadata + readme. COVERPAGE header row
     includes `ACCESSION_NUMBER, REPORTCALENDARORQUARTER, ISAMENDMENT, AMENDMENTNO,
     AMENDMENTTYPE, ...` (observed in the zip).
   - Table documentation: https://www.sec.gov/files/form_13f_readme.pdf (downloaded
     2026-08-12; table-of-contents lists the same 7 tables).

### A.5 Rate limits and fair use

Source: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
(retrieved 2026-08-12), quoting:

- "Current max request rate: **10 requests/second**."
- "Please declare your user agent in request headers" — sample:
  `User-Agent: Sample Company Name AdminContact@<sample company domain>.com`, plus
  `Accept-Encoding: gzip, deflate` and `Host: www.sec.gov`.
- "The SEC does not allow botnets or automated tools to crawl the site" outside the
  acceptable policy; SEC "reserves the right to limit request rates".
- Observed behaviour: requests without a declared UA got **HTTP 403** (WebFetch
  default UA was blocked, 2026-08-12); the same URLs with a declared UA succeeded.
- Indexes update nightly from ~10:00 p.m. ET; filings accepted after 5:30 p.m. ET
  disseminate the next business day.

### A.6 Amendments (13F-HR/A) and restated tables

- Amendments appear as a separate submission with form type `13F-HR/A` in the
  submissions API and indexes — **observed live**: Berkshire shows `13F-HR/A`
  2025-08-14 filed the same day as the original Q2 `13F-HR`, and two `13F-HR/A`
  2024-05-15 (submissions JSON, A.2).
- The amendment's cover page carries the semantics — observed in
  `primary_doc.xml` of accession 0000950123-25-008361:
  `reportCalendarOrQuarter = 03-31-2025`, `amendmentNo = 1`,
  **`amendmentType = NEW HOLDINGS`**, `tableEntryTotal = 4` (an add-only table of 4
  positions, here previously confidential D.R. Horton / Lennar / NUE positions —
  issuers observed in the infotable XML).
- `amendmentType` takes the value `RESTATEMENT` or `NEW HOLDINGS`: a RESTATEMENT
  **replaces** the original table in full; NEW HOLDINGS is **additive** to it.
  The two enum values are observed as a COVERPAGE.tsv column (`AMENDMENTTYPE`) and
  NEW HOLDINGS was observed live; the replace-vs-add semantics are per Form 13F
  instructions **[semantics not re-verified against the instructions PDF today —
  treat as to-confirm when writing the merge logic]**.
- Implication for the pipeline: holdings-as-of-quarter = last RESTATEMENT (or the
  original 13F-HR if none) **plus** all subsequent NEW HOLDINGS amendments, ordered
  by amendment number. **[inferred from the above]**

### A.7 Feasibility: 8 quarters × 20 managers

- Volume: ~160 original filings + a handful of amendments; ~2 XML fetches per filing
  plus one submissions JSON per manager ≈ **~360–420 HTTP requests total**, each file
  typically a few KB to a few hundred KB. At even half the permitted 10 req/s this is
  **~1–2 minutes of wall time — trivially feasible** [arithmetic from observed counts].
- Alternative bulk path: 8 DERA quarterly zips ≈ 800 MB compressed / ~3.2 GB of
  INFOTABLE.tsv to filter down to 20 CIKs [extrapolated from the one observed
  quarter]. Heavier download, but zero per-filer request logic and SEC-flattened
  amendment columns included.
- History depth is no constraint: EDGAR indexes go back to 1994Q3; DERA 13F data sets
  back to 2013 Q2. One real-world caveat found: **Situational Awareness LP (CIK
  0002045724) has only 6 quarters of 13F-HRs — first filing 2025-02-12** — so 8
  quarters of history simply does not exist for the newest manager
  (https://data.sec.gov/submissions/CIK0002045724.json, retrieved 2026-08-12). A
  second sibling filer "Situational Awareness Partners LP" (CIK 0002038540) filed its
  first 13F-HR 2026-05-18 — entity disambiguation needed for this manager.

---

## B) Dataroma (https://www.dataroma.com)

### B.1 Manager coverage

Home page https://www.dataroma.com/m/home.php (retrieved 2026-08-12) lists ~85
tracked "Superinvestors". **All 16 target managers are present**, with these portfolio
codes (`/m/holdings.php?m=CODE`):

| Manager | Code | Manager | Code |
|---|---|---|---|
| Maverick Capital (Ainslie) | mc | Berkshire Hathaway (Buffett) | BRK |
| Viking Global | vg | Lone Pine (Mandel) | LPC |
| Greenlight (Einhorn) | GLRE | Appaloosa (Tepper) | AM |
| Icahn Capital | ic | Tiger Global (Coleman) | TGM |
| Fairholme (Berkowitz) | fairx | Giverny (Rochon) | GC |
| Pershing Square (Ackman) | psc | Leon Cooperman | oa |
| Third Point (Loeb) | tp | TCI (Hohn) | tci |
| Fundsmith (Smith) | FS | Lindsell Train | LT |

### B.2 What it adds beyond raw EDGAR (observed on the BRK pages, 2026-08-12)

- **Buy/sell activity classification per quarter**: `/m/m_activity.php?m=BRK&typ=a`
  (typ=b buys only, typ=s sells only) renders rows with CSS classes `td.buy` /
  `td.sell` and pre-computed labels — observed values "Buy", "Add 203.99%",
  "Add 43.24%" plus share-change counts. This is Dataroma's own quarter-over-quarter
  diff of the filings — the classification does not exist in EDGAR.
- **History depth**: activity pages paginate via `&L=1..9` for BRK; page L=9 shows
  years 2012–2013 → **13+ years of quarterly activity**, far beyond 8 quarters.
- **Per-stock position history**: `/m/hist/hist.php?f=BRK&s=AAPL` links per holding;
  portfolio history at `/m/hist/p_hist.php?f=BRK`.
- Current-price/52-week enrichment on the holdings page (reported price vs current).

### B.3 Page structure for scraping (observed 2026-08-12)

Plain server-rendered PHP/HTML, no JS rendering needed. Holdings page
(`/m/holdings.php?m=BRK`, 25 KB) is a single `<table>`: per row — history link, stock
(ticker + name), % of portfolio, recent-activity cell, shares, reported price, value,
then current-quote columns. Semantic CSS classes (`shares`, `val`, `buy`, `sell`,
`quote`) make parsing straightforward.

### B.4 Robots.txt / terms of use

- **robots.txt: none served.** Both `https://www.dataroma.com/robots.txt` and
  `/m/robots.txt` return **302 → /m/home.php** with empty body (observed via curl -i,
  2026-08-12) — i.e., no crawl rules are published.
- Terms of Service (https://www.dataroma.com/m/inc/tos.php, retrieved 2026-08-12):
  no clause addressing automated access or scraping. The restrictive clause is
  **content ownership/republication** — quoting clause 4: "The content provided on
  this site is owned by Dataroma.com. **No republishing, reproducing, redistributing
  or selling of the content is allowed.** However, you are free to publish small
  portions of the content for reference purposes, provided you cite Dataroma.com as
  the source and include a link to the relevant page."
- Also note clause 3: no guarantee of accuracy or completeness.
- **[inferred]** Systematically ingesting Dataroma tables into a firm pipeline sits
  in tension with clause 4's no-reproduction language even though scraping per se is
  not mentioned; the underlying facts (holdings) are public-domain SEC data, but
  Dataroma's derived classifications are claimed as owned content.

---

## C) WhaleWisdom (https://whalewisdom.com)

### C.1 Coverage of the 4 WhaleWisdom-only names (checked 2026-08-12)

WhaleWisdom ingests all EDGAR 13F filers, so coverage is effectively universal:

- **Situational Awareness LP** — https://whalewisdom.com/filer/situational-awareness-lp
  → HTTP 200, title "SITUATIONAL AWARENESS LP Top 13F Holdings".
- **Atreides Management** — https://whalewisdom.com/filer/atreides-management-lp
  → HTTP 200, "ATREIDES MANAGEMENT, LP Top 13F Holdings".
- **Coatue Management** — https://whalewisdom.com/filer/coatue-management-llc
  → HTTP 200, "COATUE MANAGEMENT LLC Top 13F Holdings".
- **Altimeter** — `filer/altimeter-capital-management-lp` → **404**;
  https://whalewisdom.com/filer/altimeter-partners-fund-lp → HTTP 200, "ALTIMETER
  PARTNERS FUND LP Top 13F Holdings". Web search (2026-08-12) shows several Altimeter
  entities on WhaleWisdom (Partners Fund, Private SPV/Partners funds, Growth Corps).
  **[unverified]** which slug corresponds to the management-company 13F filer of
  record (EDGAR filer "Altimeter Capital Management, LLC/LP", CIK 1541617 per SEC
  archives found in the same search) — needs a one-time manual disambiguation.

### C.2 Free vs paid tiers

Source: https://whalewisdom.com/pricing (retrieved 2026-08-12):

- **Free**: "View Past 2-Years of 13F Data", email alerts, small fund groups /
  watchlists, backtests limited to 2 years, "Access to most tools on the site with
  limited data". "There are no trial accounts, but much of WhaleWisdom is accessible
  for free without any subscription."
- **Standard — $90/quarter**: no ads, historical 13F back to 2001 for up to 50 funds
  and 50 stocks per 90 days, **API Access**, Excel export (3,000 records/download,
  some tools excluded), Excel add-in.
- **Pro — $150/quarter**: history quota 200 funds / 200 stocks per 90 days, "Export
  13F Data" option on watchlists, combined holdings report, full backtester.
- **Enterprise — "Please contact us"**: up to 5 seats, **"Unlimited 13F data through
  API"**, **"Nightly FTP files for 13F and Schedule 13D/G"**.

### C.3 API

Source: https://whalewisdom.com/help/api (retrieved 2026-08-12):

- REST endpoint `https://whalewisdom.com/shell/command`; requires a registered
  account; API keys created in the user profile; requests signed with a
  shared-key + secret-key digital signature (or session cookie in-browser).
- Rate limit: **20 requests per minute**.
- Access tiers, quoting: "Subscribers have full access to all quarterly 13F data.
  **Non-subscribers have access to the last 8 quarters worth of data not including
  the current quarter.**" — i.e., the free API window is exactly 8 trailing quarters
  but always excludes the most recent quarter, so the newest filing round would be
  paywalled. (Not tested — would require creating an account, which was out of scope.)

### C.4 Terms of use on automation

Source: https://whalewisdom.com/legal/terms_of_use (retrieved 2026-08-12), quoting:

- "**Use of automated scripting tools to crawl the site or attempting to bypass the
  API is strictly prohibited** and may result in termination of your subscription.
  Excessive requests may result in throttling."
- License is "only for internal business use or personal, noncommercial use"; "In no
  event shall the User publish, sell, lease, disseminate, retransmit, redistribute,
  broadcast, circulate or otherwise reproduce, provide or permit access to any
  WhaleWisdom Information in any format to anyone" (limited quotation carve-outs
  follow).
- robots.txt (https://whalewisdom.com/robots.txt, retrieved 2026-08-12) explicitly
  **Disallows** the useful paths: `/filer/holdings`, `/filer/holdings_csv|_tsv|_xlsx`,
  `/stock/holdings*`, `/filing/view/`, `/filer/summary`, etc.
- Net: scraping WhaleWisdom is both robots-disallowed and TOU-prohibited; the
  sanctioned automation path is the keyed API (free = trailing-8-quarters-minus-
  current; current-quarter access requires Standard $90/qtr or above).

---

## Implications for the source-of-truth decision (facts and trade-offs only)

1. **EDGAR fully covers the stated need on its own.** 8 quarters × 20 managers is
   ~400 small requests (~minutes at the permitted 10 req/s with a declared
   User-Agent), against filer-provided XML with a stable schema, back to 2013 in
   structured bulk form and 1999+ (13F XML era much later; text era before) via
   archives. Amendments are explicit and machine-readable (`amendmentType`
   RESTATEMENT vs NEW HOLDINGS on the cover page / COVERPAGE.tsv). No terms-of-use
   friction and no fees. Costs: we must build the CIK mapping, amendment-merge logic,
   and quarter-diff (buy/sell) logic ourselves; CUSIP→ticker mapping is not in the
   13F data.
2. **Dataroma adds derived value (buy/sell/add/reduce classification, 13 years of
   per-manager activity, per-stock history) and covers all 16 target managers**, with
   trivially parseable HTML and no robots.txt; but its TOS claims ownership of the
   content and forbids republishing/reproduction beyond small cited excerpts, and it
   guarantees no accuracy. It publishes no update-latency SLA and covers only its
   curated ~85 managers.
3. **WhaleWisdom covers everything (including all 4 non-Dataroma names, modulo one
   Altimeter slug to disambiguate) and has a real API**, but scraping is explicitly
   prohibited (TOU + robots.txt), the free API excludes the current quarter and is
   limited to 8 trailing quarters and 20 req/min, and current-quarter API access
   costs $90/quarter minimum with 50-fund/90-day history quotas at that tier.
4. **Data-provenance rule fit**: firm rules require primary sources first; EDGAR is
   the primary source both aggregators themselves ingest. Anything taken from
   Dataroma/WhaleWisdom is redistribution-restricted derived content; anything from
   EDGAR is unrestricted public data.
5. **Known edge cases to carry into ticket 03**: Situational Awareness has only 6
   quarters of filings (first 2025-02-12) plus a second sibling filer entity;
   Berkshire-style multi-manager filings use `otherManager` fields; amendment merge
   semantics (RESTATEMENT replaces / NEW HOLDINGS adds) should be confirmed against
   the Form 13F instructions before coding.
