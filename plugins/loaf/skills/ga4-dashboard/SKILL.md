---
name: ga4-dashboard
description: >-
  Launch the Loaf "GA4 Dashboard" — a web analytics dashboard pulling live from
  the loaf-composite connector (GA4) and rendering sessions, users, engagement,
  transactions, revenue, and conversion rate with a 7/30/90-day toggle, channel
  breakdown, and top landing pages. Use when someone wants a web-traffic view
  — "how's the website", "sessions and engagement", "which channel converts
  best", "GA4 overview", "web conversion", "channel performance", "top landing
  pages". Not for full-funnel sales (use trading-dashboard) or sales-only views
  (use sales-dashboard).
---

# Loaf GA4 Dashboard

A single self-contained HTML artifact (`assets/ga4-dashboard.html`) that renders a
web analytics dashboard for loaf.com, pulling live from the **`loaf-composite`**
connector (GA4 tools).

- **Source:** `ga4_official_run_report` against property `256796183` (loaf.com).
- **Pull-once, slice in memory.** A single LOOKBACK_DAYS daily pull of sessions,
  users, engaged sessions, transactions, and purchase revenue is fetched on open.
  All 7/30/90 windows are sliced from that in memory. Channel and landing-page
  breakdowns fetch per window (cached for revisits).

## How to launch

1. **Confirm the connector.** The `loaf-composite` MCP server ships with this
   plugin. If missing, the dashboard shows "connector bridge unavailable".

2. **Verify the tool name.** Defaults to
   `mcp__loaf-composite__ga4_official_run_report`. Discover the real name via
   ToolSearch (search `ga4_official_run_report`) and update `CFG.T_GA4` if the
   server is mounted under a different ID.

3. **Confirm the GA4 property.** `CFG.GA4_PROPERTY` defaults to `256796183`
   (loaf.com). Verify it matches the property the connector is authed to.

4. **Open as a Cowork artifact.** The `<script id="cowork-artifact-meta">` header
   grants the loaf-composite connector automatically.

## Config knobs

| Key | Default | Notes |
|---|---|---|
| `TODAY` | `""` | `""` = real current date. Pin for staging. |
| `REF_DATE` | `"auto"` | Auto-detects last day with data. |
| `DEFAULT_DAYS` | `7` | Initial window (7/30/90). |
| `LOOKBACK_DAYS` | `200` | Base pull window. |
| `GA4_PROPERTY` | `256796183` | loaf.com property. |
| `T_GA4` | `mcp__loaf-composite__ga4_official_run_report` | Verify per host. |

## What it shows

- **KPIs:** Sessions, active users, engagement rate, transactions, GA4 purchase
  revenue, web conversion rate — each with vs-prior delta.
- **Sessions trend:** Daily sessions bars with conversion rate overlay (secondary
  axis) — lets you see traffic volume vs quality at a glance.
- **Channel mix doughnut:** Sessions share by `sessionDefaultChannelGroup`.
- **Top channels table:** Sessions, share, transactions, conv rate, revenue — click
  a row to explore in chat.
- **Top landing pages table:** Page path, sessions, bounce rate, transactions — click
  a row to explore in chat.
- **Insight cards:** Traffic momentum, best-converting channel, conversion rate trend,
  top landing page — each wired to an "Explore →" follow-up prompt.

**Note on revenue.** GA4 `purchaseRevenue` only captures web ecommerce events and
may undercount vs the loaf connector (which is the source of record). Use the GA4
figure for trend/ratio analysis; use the loaf connector for absolute revenue numbers.
