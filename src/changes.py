"""Quarter-over-quarter significant-change tables, regenerated into data/out/changes/.

Significant change (CONTEXT.md): always new buys and full exits; adds/trims with
share-count change >=25% of the prior holding where the position is >=0.5% of the
portfolio; any change of >=1 percentage point of portfolio weight. Measured in share
counts, never value. Main book only (sh_prn_type SH, no put/call).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from common import HOLDINGS, OUT

CHANGE_COLUMNS = ["cusip", "ticker", "issuer", "class", "action", "shares_prev", "shares_cur",
                  "delta_shares", "pct_change_shares", "weight_prev_pct",
                  "weight_cur_pct", "delta_weight_pp", "value_cur_usd"]


def load_main_book(path: Path) -> dict[str, dict]:
    """Aggregate a holdings CSV to the main book: shares + value by CUSIP."""
    book: dict[str, dict] = defaultdict(lambda: {"shares": 0, "value": 0,
                                                 "issuer": "", "ticker": "",
                                                 "cls": ""})
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["sh_prn_type"] != "SH" or row["put_call"]:
                continue
            entry = book[row["cusip"]]
            entry["shares"] += int(float(row["shares"] or 0))
            entry["value"] += int(float(row["value_usd"] or 0))
            entry["issuer"] = entry["issuer"] or row["issuer"]
            entry["ticker"] = entry["ticker"] or row["ticker"]
            entry["cls"] = entry["cls"] or row["class"]
    return dict(book)


def classify(prev: dict[str, dict], cur: dict[str, dict]) -> list[dict]:
    total_prev = sum(e["value"] for e in prev.values()) or 1
    total_cur = sum(e["value"] for e in cur.values()) or 1
    changes = []
    for cusip in sorted(set(prev) | set(cur)):
        p, c = prev.get(cusip), cur.get(cusip)
        sh_p = p["shares"] if p else 0
        sh_c = c["shares"] if c else 0
        if sh_p == sh_c:
            continue
        w_p = (p["value"] / total_prev * 100) if p else 0.0
        w_c = (c["value"] / total_cur * 100) if c else 0.0
        pct = (sh_c - sh_p) / sh_p * 100 if sh_p else None

        if p is None or sh_p == 0:
            action = "new"
        elif c is None or sh_c == 0:
            action = "exit"
        else:
            big_share_move = abs(sh_c - sh_p) >= 0.25 * sh_p and max(w_p, w_c) >= 0.5
            big_weight_move = abs(w_c - w_p) >= 1.0
            if not (big_share_move or big_weight_move):
                continue
            action = "add" if sh_c > sh_p else "trim"

        ref = c or p
        changes.append({
            "cusip": cusip, "ticker": ref["ticker"], "issuer": ref["issuer"],
            "class": ref["cls"], "action": action, "shares_prev": sh_p, "shares_cur": sh_c,
            "delta_shares": sh_c - sh_p,
            "pct_change_shares": f"{pct:.1f}" if pct is not None else "",
            "weight_prev_pct": f"{w_p:.2f}", "weight_cur_pct": f"{w_c:.2f}",
            "delta_weight_pp": f"{w_c - w_p:.2f}",
            "value_cur_usd": c["value"] if c else 0,
        })
    order = {"new": 0, "exit": 1, "add": 2, "trim": 3}
    changes.sort(key=lambda r: (order[r["action"]], -abs(int(r["value_cur_usd"] or 0))))
    return changes


def regenerate_all() -> int:
    """(Re)write data/out/changes/<manager>/<qkey>.csv for every consecutive pair."""
    n_files = 0
    for mgr_dir in sorted(HOLDINGS.iterdir()):
        if not mgr_dir.is_dir():
            continue
        quarters = sorted(p.stem for p in mgr_dir.glob("*.csv"))
        for prev_q, cur_q in zip(quarters, quarters[1:]):
            changes = classify(load_main_book(mgr_dir / f"{prev_q}.csv"),
                               load_main_book(mgr_dir / f"{cur_q}.csv"))
            out_dir = OUT / "changes" / mgr_dir.name
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / f"{cur_q}.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=CHANGE_COLUMNS)
                w.writeheader()
                w.writerows(changes)
            n_files += 1
    return n_files


if __name__ == "__main__":
    print(f"wrote {regenerate_all()} change tables under {OUT / 'changes'}")
