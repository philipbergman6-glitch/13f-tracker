# 06 — Reconnect TradingView MCP and verify watchlist WRITE capability

Type: task
Status: open
Blocked by: 13 (boss go/no-go — no TradingView work until the boss approves the push;
Philip, 2026-08-12)

## Question

The TradingView MCP is installed but disconnected, and the setup memory
(`tradingview-mcp-setup`) confirms watchlist READS were verified — not writes. Before
watchlist design (ticket 07) can be decided: reconnect the MCP (follow the memory
note's launch procedure — MSIX local-copy quirk, profile sync, `--remote-debugging-port`,
maximize window before diagnosing), then verify whether the MCP (or the authenticated
`symbols_list` API pattern noted in memory) can CREATE a watchlist and ADD/REMOVE
symbols. Record: exact working procedure, which write operations work, and any limits
(symbol count, rate). Do not touch the existing "13F" watchlist.
