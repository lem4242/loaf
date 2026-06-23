---
name: sales-dashboard
description: >-
  Launch the Loaf "Sales Dashboard" — a sales-only executive dashboard pulling live
  from the loaf connector and rendering revenue, orders, AOV, and channel mix
  (Web / POS / OMS) in one interactive Cowork artifact with a 7/30/90-day
  toggle and stacked daily channel trend. Use when someone wants a pure sales
  view without web analytics — "how are sales by channel", "POS vs web
  breakdown", "orders and AOV", "revenue by channel", or any sales-only
  overview. Not for web traffic (use ga4-dashboard) or a combined view (use
  trading-dashboard).
---

# Loaf Sales Dashboard

A single self-contained HTML artifact (`assets/sales-dashboard.html`) that renders a
channel-level sales dashboard for Loaf, pulling live from the **`loaf`** connector.

- **Source of record:** `get_sales_aggregate` (daily orders by `order_location` —
  Web, POS, OMS) sliced in memory for any window. Product and category breakdowns
  fetched per window, cached for revisits.
- **No GA4 dependency.** All data comes from the loaf connector.

## How to launch

1. **Confirm the connector is present.** The `loaf` MCP server ships with this
   plugin (see `.mcp.json`). If missing, the dashboard shows "connector bridge
   unavailable".

2. **Verify the tool name.** The artifact's `CFG` block defaults to
   `mcp__plugin_loaf_loaf__get_sales_aggregate`. Tool names are instance-specific — if the loaf
   server is mounted under a different ID, discover the real name via ToolSearch
   (search `get_sales_aggregate`) and update `CFG.T_SALES` before opening.

3. **Open it as a Cowork artifact.** The `<script id="cowork-artifact-meta">` header
   declares the required tool and server, so the host grants access automatically.
   The dashboard auto-detects the last complete day of data — no date input needed.

## Config knobs

| Key | Default | Notes |
|---|---|---|
| `TODAY` | `""` | `""` = real current date. Pin e.g. `"2026-06-01"` for staging data. |
| `REF_DATE` | `"auto"` | Auto-detects last complete day. Pin to override. |
| `DEFAULT_DAYS` | `7` | Initial window (7/30/90). |
| `LOOKBACK_DAYS` | `200` | Single base pull covers 90-day view + 90-day prior with slack. |
| `T_SALES` | `mcp__plugin_loaf_loaf__get_sales_aggregate` | Verify per host. |

## What it shows

- **KPIs:** Total revenue, orders, blended AOV, Web revenue, POS revenue, OMS revenue
  — each with vs-prior-period delta.
- **Stacked trend chart:** Daily revenue bars coloured by channel (Web / POS / OMS)
  so you can see channel composition shift day-by-day.
- **Channel mix doughnut:** Share of revenue by order location for the window.
- **Top products:** Click a row to drill down in chat.
- **Product types:** Horizontal bars by category (tier-2).
- **Insight cards:** Channel momentum, AOV gap (web vs POS), category concentration,
  top product — each with an "Explore →" button that sends a follow-up prompt.
