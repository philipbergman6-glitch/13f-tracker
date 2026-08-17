# Filer-status exceptions

## Situational Awareness Partners LP (CIK 2038540) — 2026Q2 LATE — RESOLVED 2026-08-17

Resolution (analyst decision, Philip, 2026-08-17): scoped CIK 2038540 to
2026Q1-only in `manager_map.csv` (`to_quarter=2026Q1`). Basis:

- Schedule 13G (acc 0000935836-26-000303, Nebius Group, filed re event date
  2026-05-19; https://www.sec.gov/Archives/edgar/data/1513845/000093583626000303/,
  retrieved 2026-08-17) states "Adviser is the investment adviser to the Fund",
  naming Situational Awareness LP (CIK 2045724) as Adviser and Situational
  Awareness Partners LP (CIK 2038540) as Fund, with identical share counts
  attributed jointly across the reporting persons.
- The Fund's only 13F ever (2026Q1) was an exact duplicate of the Adviser's book
  (status DUPLICATE in filer_status.csv), so the Adviser's 13F-HR carries the
  consolidated portfolio.
- WhaleWisdom shows no separate Q2 portfolio for the Fund (consistent with EDGAR).

This is a portfolio-coverage decision, not a legal conclusion that CIK 2038540
had no filing obligation. Monitor the CIK for renewed 13F filings; if one
appears, revisit the map entry.

Original detection record below.

## Situational Awareness Partners LP (CIK 2038540) — 2026Q2 LATE

Detected 2026-08-17 by the new filer-status gate (`data/holdings/filer_status.csv`).

Source: EDGAR submissions JSON for CIK 2038540 (data.sec.gov/submissions/CIK0002038540.json,
retrieved 2026-08-17): the entity's only 13F filing ever is the 2026Q1 13F-HR
(acc 0002038540-26-000004, filed 2026-05-18). No 13F-HR and no 13F-NT for period
2026-06-30 as of 2026-08-17; the Rule 13f-1 deadline was 2026-08-14.

Effect: pipeline exits 1 and withholds (re)writing `data/holdings/situational-awareness/2026Q2.csv`.
The previously committed 2026Q2 CSV (LP-only, 26 rows) remains in place and is
content-identical to what an unblocked run would write.

Context: in 2026Q1 this filer's book was an exact duplicate of Situational Awareness LP's
(status DUPLICATE, 42 rows). Plausible explanations, unverified:
1. The entity no longer has a 13F obligation (book consolidated under the LP) and
   should get `to_quarter=2026Q1` in `manager_map.csv`.
2. The filing is genuinely late and will appear; re-run then.

Resolution requires an analyst decision — do not set `to_quarter` without evidence
(e.g. a 13F-NT, an adviser-level ADV change, or the Q2 filing appearing).
