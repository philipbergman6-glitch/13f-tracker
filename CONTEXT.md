# 13F Tracker

Quarterly pipeline tracking SEC 13F holdings for a fixed 16-manager list, feeding a
static HTML dashboard and per-manager TradingView watchlists.

## Language

**Manager**:
One of the 16 names on Philip's fixed list — the human-level identity a dashboard line
represents. A Manager aggregates one or more Filers across time.
_Avoid_: fund, firm, investor (ambiguous with Filer)

**Filer**:
A single SEC EDGAR filing entity with its own CIK that files 13F-HR. Several Filers can
belong to one Manager (dual entities, successions).
_Avoid_: company, entity

**Manager mapping**:
The committed table mapping each Manager to its Filer CIKs with the quarter range each
CIK is valid for — the only place succession/aggregation knowledge lives.

**Quarter-final holdings**:
A Manager's holdings for a quarter after amendment merge: latest RESTATEMENT (or the
original 13F-HR if none) plus all subsequent NEW HOLDINGS amendments in order. This is
what gets committed and what all downstream views derive from.
_Avoid_: latest filing, current holdings

**Significant change**:
A quarter-over-quarter change worth surfacing: any new buy or full exit; any add/trim
with share-count change ≥25% of the prior holding where the position is ≥0.5% of the
portfolio; any change of ≥1 percentage point of portfolio weight. Measured in share
counts, never value (value moves with price).
_Avoid_: notable move, big change

**Main book**:
A Manager's shares-only 13F positions — what "top positions" and portfolio value mean
on the dashboard. Puts/calls are stored but shown separately, never summed into it.

**Regulatory AUM (gross)**:
The Form ADV Item 5F RAUM figure used as the external AUM comparison. Gross, so it can
exceed net AUM for levered funds — always labelled as such.
_Avoid_: AUM (unqualified)
