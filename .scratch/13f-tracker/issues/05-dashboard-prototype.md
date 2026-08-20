# 05 — Dashboard prototype (one manager, mock data)

Type: prototype
Status: resolved (2026-08-12, with Philip)
Blocked by: 03 (resolved — unblocked)

## Question

Build a throwaway static-HTML dashboard prototype for ONE manager using realistic mock
or first-parsed data, covering the full content brief (portfolio value vs AUM, top
positions, changes, industry pattern, plus a sketch of the cross-manager summary table)
so Philip can react to layout, depth, and visual standard ("$10,000 report" bar) before
the real build. Invoke `/dataviz` and `/prototype`. Links the prototype as an asset;
resolution records what Philip wants kept/changed.

## Progress (2026-08-12)

Prototype built and awaiting Philip's reaction — not yet resolved.

- **Asset:** `prototypes\13f-dashboard-prototype.html` (self-contained; double-click, or
  serve locally). Three structurally different variants via `?variant=` / bottom bar /
  arrow keys: **A — Quarterly report** (single-column narrative, "$10k report" style),
  **B — Desk terminal** (dense grid + 20-manager rail, full holdings table),
  **C — Cross-manager first** (consensus-moves landing + manager cards + drill-down).
- **Data is REAL**: Berkshire 13F-HR Q1-2026 (acc 0001193125-26-226661, filed 2026-05-15)
  vs Q4-2025 (acc 0001193125-26-054580), parsed from EDGAR 2026-08-12; raw XML kept at
  `data\raw\prototype-ticket05\`. AUM comparator = 10-Q equity securities FV $323.8bn
  (2026-06-30). Change list uses ticket-03 thresholds → 22 significant changes.
- Prototype shortcuts (fine here, not for the build): hand-made sector/ticker maps,
  no amendment merge, cross-manager table is labelled mock.

## Answer

Resolved 2026-08-12 with Philip, who reviewed all three variants and accepted the
recommendation, adding one hard requirement:

1. **Layout: hybrid — C's landing with A's depth.** The dashboard lands on the
   cross-manager view (consensus buys/sells table + 20 manager cards); clicking a
   manager opens variant A's report-style page for that manager (hero tiles, top
   positions, significant-changes table, sector mix). Variant B (desk terminal) is
   not the skeleton; its full-holdings table survives as an expandable section
   inside each manager page.
2. **Depth: written takeaways per manager.** 2–3 generated sentences per manager per
   quarter saying what the moves amount to, on top of the prototyped data sections.
   Full holdings behind an expand, not top-N only.
3. **Content brief unchanged** for the first real build. Cross-manager analytics
   beyond the summary table, and 8-quarter history charts, stay in the map's fog
   until the first build exists.
4. **Philip's added bar (verbatim intent): the real dashboard must be *genuinely* a
   "$10,000 visually designed" product** — the prototype's plain styling is NOT the
   accepted standard; it validated structure only. The build ticket must treat visual
   design as a first-class requirement (typography, spacing, color system, polish),
   not an afterthought.

Carried into new build ticket 11. Prototype asset stays at
`prototypes\13f-dashboard-prototype.html` (throwaway — structure reference only).
