---
name: trading-dashboard
description: >-
  Launch the Loaf "Trading Dashboard" — a fast, on-brand executive dashboard that
  pulls live from the loaf (sales) and loaf-composite (GA4) connectors and
  renders revenue, orders, AOV, channel mix, top products, web sessions and
  acquisition in one interactive Cowork artifact with a 7/30/90-day toggle. Use
  this whenever someone wants a Loaf sales/trading overview, a KPI dashboard, a
  "how's trading", "sales dashboard", "revenue dashboard", "loaf numbers", or a
  visual summary of Loaf performance over a period — even when they don't name
  the connectors. Not for one-off figures (call get_sales_aggregate or
  ga4_official_run_report directly for a single number); this builds the
  standing dashboard.
---

# Loaf Trading Dashboard

A single self-contained HTML artifact (`assets/trading-dashboard.html`) that renders
an interactive trading dashboard for Loaf. It reads **live** from two connectors
in this plugin:

- **`loaf`** — sales (orders, products, product types) via `get_sales_aggregate`.
  The source of record for revenue/orders/AOV across **all** channels (Web, POS, OMS).
- **`loaf-composite`** — GA4 via `ga4_official_run_report`. Supplies **web traffic
  only** (sessions, channel groups, transactions). Web conversion = web orders ÷ sessions.

The artifact talks to the connectors itself through the host's
`window.cowork.callMcpTool` bridge — you don't fetch the data; you launch the
artifact and it pulls on open.

## How to launch

1. **Confirm both connectors are present.** This skill ships with the `loaf` and
   `loaf-composite` MCP servers (see the plugin's `.mcp.json`). If either is
   missing, the dashboard shows a "connector bridge unavailable" / load error.

2. **Verify the tool names for this host.** The template's `CFG` block defaults to
   the plugin's canonical names — `mcp__loaf__get_sales_aggregate` and
   `mcp__loaf-composite__ga4_official_run_report`. Tool names are
   **instance-specific**: if a deployment mounts the servers under different IDs
   (e.g. an Obot composite with namespaced tools, or per-session connector GUIDs),
   discover the real names via ToolSearch (search `get_sales_aggregate` /
   `ga4_official_run_report`) and set `CFG.T_SALES` / `CFG.T_GA4` to match before
   opening. Treat the tool name as the **function**, not a literal string.

3. **Set the GA4 property.** `CFG.GA4_PROPERTY` defaults to loaf.com (`256796183`).
   Confirm it's the right property for the account this connector is authed to.

4. **Open it as a Cowork artifact.** The `<script id="cowork-artifact-meta">`
   header already declares `mcpTools` + `mcpServerNames`, so the host grants the
   right connectors. The dashboard auto-detects the last complete day of data —
   no date input needed.

That's it. The 7/30/90 toggle, click-to-explore rows (they call
`cowork.sendPrompt` to start a drill-down chat), KPIs, charts and insight cards
all work with no further wiring.

## Config knobs (top of the `<script>` in the template)

| Key | Default | Notes |
|---|---|---|
| `TODAY` | `""` | `""` = real current date (production). **Demo on staging data:** pin to the last day with data, e.g. `"2026-06-01"`, so windows land on real numbers instead of empty recent days. |
| `REF_DATE` | `"auto"` | `"auto"` = detect the last complete day from the data already pulled. Pin a date to override. |
| `DEFAULT_DAYS` | `7` | Initial window (7/30/90). |
| `LOOKBACK_DAYS` | `200` | The single window pulled once and sliced in memory; covers the 90-day view + its 90-day prior with slack. |
| `GA4_PROPERTY` | `256796183` | loaf.com GA4 property id. |
| `T_SALES` / `T_GA4` | plugin names | The two MCP tool names — verify per host (step 2). |

## How it's built for speed (don't regress this)

Optimised for hosts that may run MCP calls **serially** (e.g. chat), where load
time is the *sum* of round-trips, not the slowest one:

- **Pull once, slice in memory.** The full `LOOKBACK_DAYS` of daily orders-by-
  location (two `get_sales_aggregate` calls, split to stay under the 500-row
  aggregate cap) + daily sessions (one `ga4_official_run_report`) are fetched
  **once**, anchored to `TODAY` (not the reference day, so there's no circular
  dependency). All 7/30/90 windows and their prior periods for revenue, orders,
  AOV, mix, trend and sessions are then **sliced from those arrays with no
  network**. Verified to reproduce the connector's own windowed aggregates exactly.
- **No date probe.** The last complete day is detected from the base data, so the
  old blocking "what's the latest day?" round-trip is gone.
- **Per-call promise cache.** `mcp()` caches by tool+args, so revisiting a tab
  fires **zero** calls and concurrent duplicate calls collapse.
- Only product/channel rankings (not derivable from daily totals) fetch per
  window — and they're cached too.

Result (serial host): first open ~6 calls (was 9, no blocking probe), first-time
30/90 switch 3 calls (was 8), **revisited tab 0 calls** (was 8).

**Watch-out:** the two-call split assumes ~3 `order_location` values. If a
deployment has more locations, `days × locations` can exceed the 500-row cap —
lower `LOOKBACK_DAYS` or chunk the base fetch into more slices.
