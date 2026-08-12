# EDGAR-only source of truth

Philip's original brief named Dataroma and WhaleWisdom as sources, but the pipeline
ingests SEC EDGAR exclusively and computes quarter-over-quarter diffs itself
(decided with Philip 2026-08-12, wayfinder ticket 03). Reasons: EDGAR fully covers
the need (~400 small requests for 8q × 20 managers, stable filer XML, machine-readable
amendments, free); Dataroma's TOS forbids reproducing its derived content; WhaleWisdom
bans scraping and its free API excludes the current quarter — the one that matters each
cycle; and the firm's primary-source rule points the same way. The aggregators remain
manual eyeball cross-checks during QA only — never ingested. Evidence:
`notes/research/02-data-source-landscape.md`.
