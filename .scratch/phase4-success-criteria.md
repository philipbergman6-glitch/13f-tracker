# Phase 4 success criteria (defined before coding, 2026-08-17)

Expected outputs: modified src/dashboard.py + src/dashboard_template.html,
new tests, regenerated dashboard/index.html, screenshots at 6 widths,
notes/phase4-dashboard.md. No changes under data/.

1. Mobile/layout: at 1440, 1280, 1024, 768, 390, 360 px the landing page and
   the widest manager page report document.scrollWidth <= viewport width
   (measured in a real headless Chrome, not by inspection). Table panels may
   scroll internally. Screenshots captured at all widths, desktop unchanged
   in character.
2. Combined value: hero label + a visible footnote state it is an overlapping
   sum of reported 13F long values — not firm AUM, not investable capital
   (multi-book managers; 13F excludes shorts/cash/most non-US listings).
3. Largest move: takeaway ranks moves by dollar magnitude of the position
   change (new=cur value; exit=prior value via prev weight x prev book;
   add/trim=|delta shares| x implied price). Unit test: a small new position
   must NOT headline over a multi-billion add/trim.
4. Consensus: rows ordered n_managers desc then combined $ desc (conviction
   first); section capped per side with an explicit "+N more" line (no silent
   truncation).
5. Methodology reachable without hover: visible footer methodology (linkable
   anchor), tooltips also open on tap/focus; no content exists ONLY in a
   title attribute.
6. Footer: stale "Q2 2026 filings (due 2026-08-14) enter after the
   post-deadline re-pull" sentence removed; generation metadata current.
7. Status strip: visible "Data through <quarter> · Generated <UTC timestamp> ·
   checks passed/failed/unknown (errors/warnings)" sourced from
   data/out/run_status.json at build time; unit tests cover ok / failed /
   missing states; nothing hardcoded.

Gates before commit:
- python3 -m unittest discover -s tests → all pass (>=111 + new).
- Regenerate via normal path: python3 src/dashboard.py (run-status gate on).
- git status shows NO modification to data/holdings/**, filer_status.csv.
- Displayed holdings numbers unchanged (labeling/ranking/presentation only);
  any numeric diff = bug, report not ship.
