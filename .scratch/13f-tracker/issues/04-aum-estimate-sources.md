# 04 — Where to get total-AUM estimates per manager

Type: research
Status: resolved
Blocked by: —

## Question

The dashboard compares 13F portfolio value to each manager's **total** AUM, which 13F
does not disclose. For each of the 20 managers, find the best available AUM estimate
source and its freshness: SEC Form ADV (IAPD database — regulatory AUM, primary source),
firm websites/IR pages, and top-tier press. Note which managers have no ADV (foreign or
family-office structures) and what the fallback is. Cite URL + retrieval date per figure;
mark clearly which numbers are estimates and their as-of dates. A per-manager table is
the deliverable.

## Answer

Per-manager table: [notes/research/04-aum-sources.md](../../../notes/research/04-aum-sources.md)
(all figures retrieved 2026-08-12).

- **15 of 20 have solid regulatory figures** — Form ADV Item 5F(2)(c) RAUM, read from the
  SEC monthly compilation dated 2026-08-03 (registered advisers file `ia08032026_0.zip`):
  Situational Awareness, Altimeter, Atreides, Coatue, Maverick, Viking, Greenlight (via
  DME Capital Management, matching ticket 01's filer succession), Fairholme, Pershing
  Square, Third Point, Lone Pine, Appaloosa, Tiger Global, Fundsmith, Lindsell Train —
  plus Giverny once the entity ambiguity (Rochon's Giverny Capital Inc. vs Poppe's GCAM;
  both have RAUM) is pinned to the tracked CIK.
- **2 have comparable primary-filing figures instead of AUM**: Berkshire (10-Q equity
  securities at fair value $323.8bn / shareholders' equity $747.9bn, 2026-06-30, EDGAR
  XBRL) and Icahn (IEP indicative NAV ≈ $2.6bn, 2026-06-30, 8-K of 2026-08-05) — both
  structurally not "AUM"; label accordingly.
- **1 is press-only**: TCI ($77.1bn end-2025, Forbes 2026-01-18; ERA at SEC so no RAUM;
  needs a second independent source or FCA/Companies House before decision use).
- **1 has no public figure**: Cooperman (family office, deregistered 2018) — show 13F
  long value only, labelled.
- Refresh recipe (monthly SEC zip keyed on CRD, quarterly EDGAR pulls for BRK/IEP) is in
  the findings file. Caveat: RAUM is gross — for levered L/S funds it can be well above
  net AUM; label the dashboard column "regulatory AUM (gross)".
