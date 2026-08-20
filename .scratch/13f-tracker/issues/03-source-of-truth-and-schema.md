# 03 — Decide source of truth & storage schema

Type: grilling
Status: resolved (2026-08-12, with Philip)
Blocked by: 01, 02 (both resolved)

## Question

Given the findings of tickets 01 and 02: what is the pipeline's source of truth (EDGAR
parse vs aggregator scrape vs hybrid), and what is the committed storage schema for
holdings across ≥8 quarters (file layout under `data\`, one table per manager-quarter vs
long table, columns, how changes are derived)? Firm rule leans EDGAR-primary; Philip's
brief named Dataroma/WhaleWisdom explicitly — reconcile with him in conversation.
Also settle here: how "significant" change thresholds are defined (graduates the
related fog item if answered).

## Answer

Resolved 2026-08-12 in conversation with Philip (all recommendations accepted).
Terminology captured in the repo's `CONTEXT.md`; the source-of-truth call recorded as
[ADR 0001](../../../docs/adr/0001-edgar-only-source-of-truth.md).

1. **Source of truth: EDGAR-only.** We parse filings and compute diffs ourselves;
   Dataroma/WhaleWisdom are manual QA cross-checks only, never ingested (their TOS
   forbid it; firm primary-source rule agrees). See ADR 0001.
2. **Manager vs filer:** one aggregated dashboard line per Manager; multiple filers
   summed and successions stitched via a committed manager→(CIK, quarter-range)
   mapping file. `filer_cik` kept on every holdings row for auditability.
3. **Storage schema:** committed per-manager-quarter CSVs at
   `data\holdings\<manager>\<YYYYQn>.csv`, columns: `filer_cik, accession, cusip,
   ticker, issuer, class, put_call, value_usd, shares, sh_prn_type, discretion,
   other_manager, vote_sole, vote_shared, vote_none`. Files hold **quarter-final
   holdings** (post-amendment-merge). Derived tables regenerate into `data\out\`
   (not committed); raw XML stays gitignored in `data\raw\`.
4. **CUSIP→ticker:** OpenFIGI free API with a committed cache table
   `data\ref\cusip_ticker.csv` including a manual-override column. Confirm OpenFIGI
   free-tier terms inside the build ticket before coding against it.
5. **Amendment logic:** quarter-final = latest RESTATEMENT (else original 13F-HR) +
   subsequent NEW HOLDINGS amendments in order; confirm replace-vs-add semantics
   against the official Form 13F instructions during the build; non-conforming
   amendment chains are flagged loudly, never silently merged.
6. **Significant change** (graduates the change-methodology fog item): always — new
   buys and full exits; adds/trims — share-count change ≥25% of prior holding AND
   position ≥0.5% of portfolio; plus any change ≥1pp of portfolio weight. Measured in
   share counts, never value. Thresholds are starting values, tunable after the first
   dashboard.
7. **Options rows:** stored fully (`put_call` column); dashboard's top positions and
   portfolio value use the shares-only **main book**, with puts/calls in a separate
   per-manager strip.
8. **Backfill timing:** backfill 8 quarters now, re-pull after the 2026-08-14 Q2
   deadline — the second run doubles as a live test of the amendment/late-filing path.
   Situational Awareness has only 6 quarters in existence; store what exists.
