# 09 — Quarterly automation & delivery

Type: grilling
Status: open
Blocked by: 05 (resolved 2026-08-12 — unblocked; dashboard form = hybrid C-landing +
A-drill-down static HTML, see ticket 11)

## Question

Graduated from fog now that the pipeline (ticket 08) exists. How does the quarterly
run happen and how do results reach the firm?

- Trigger: local script Philip runs after each 13F deadline vs a scheduled cloud task
  (note: cloud tasks can't reach this machine's repo — see the scheduled-run setup in
  `Documents\Claude\Scheduled\`; a cloud path would need the repo reachable or a
  different execution home).
- Delivery: does the regenerated dashboard go out by email (email.md rules — approved
  recipients only), as an artifact link, or is it just committed for on-demand viewing?
- Cadence details: run date relative to the 45-day deadline (many managers file on
  deadline day; amendments trail), and whether a second "amendments sweep" run is
  scheduled a few weeks later.

Needs the dashboard's final form (ticket 05) to decide what "delivery" even ships.
