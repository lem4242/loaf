---
name: growthbook-dashboard
description: >-
  Launch the Loaf "GrowthBook Dashboard" — a feature-flags and experiments snapshot
  dashboard pulling live from the loaf-composite connector (GrowthBook tools) and
  rendering flag status, stale flag alerts, running experiments, and recent
  results in one interactive Cowork artifact with an environment filter. Use when
  someone wants to see what flags are on or off, which experiments are running,
  what's stale and needs cleanup, or a general GrowthBook overview — "feature
  flags", "what experiments are running", "stale flags", "growthbook dashboard",
  "what's live in production". Not for sales or web analytics (use trading-dashboard,
  sales-dashboard, or ga4-dashboard).
---

# Loaf GrowthBook Dashboard

A single self-contained HTML artifact (`assets/growthbook-dashboard.html`) that renders
a snapshot view of the Loaf GrowthBook workspace, pulling from the **`loaf-composite`**
connector (GrowthBook MV tools).

- **Snapshot, not time-series.** GrowthBook data is current state, so there is no
  date-range toggle — instead the header has an **environment filter** (All /
  Production / Staging / Dev).
- **Three parallel fetches on open:** feature flags, experiments, stale flags.
  After that, all filtering is client-side with zero network calls.

## How to launch

1. **Confirm the connector.** The `loaf-composite` MCP server must expose
   `growthbook_mv_*` tools. Verify via ToolSearch (search `growthbook_mv`) — if
   the tools appear under a different server name, update `CFG.T_FLAGS`,
   `CFG.T_EXPS`, and `CFG.T_STALE` in the artifact's `CFG` block accordingly.
   If the loaf-composite does not include GrowthBook, a separate GrowthBook
   connector will need to be added to the plugin's `.mcp.json`.

2. **Open as a Cowork artifact.** The `<script id="cowork-artifact-meta">` header
   grants loaf-composite automatically.

## Config knobs

| Key | Default | Notes |
|---|---|---|
| `T_FLAGS` | `mcp__plugin_loaf_loaf-composite__growthbook_mv_get_feature_flags` | Verify per host. |
| `T_EXPS` | `mcp__plugin_loaf_loaf-composite__growthbook_mv_get_experiments` | Verify per host. |
| `T_STALE` | `mcp__plugin_loaf_loaf-composite__growthbook_mv_get_stale_feature_flags` | Verify per host. |

## What it shows

- **KPIs:** Total flags, enabled in selected environment, off/disabled, stale flags
  needing cleanup, running experiments, draft experiments.
- **Environment filter:** Dropdown in the header — filters KPIs and flags table to
  the selected environment (All / Production / Staging / Dev).
- **Feature flags table:** Key, enabled status per environment (coloured pills),
  stale badge, type, last updated — click a row to explore in chat.
- **Experiments table:** Name, status (running / draft / stopped), hypothesis
  (truncated), phase start date — click a row to explore in chat.
- **Stale flags alert:** If any flags are stale, a highlighted section lists them
  with cleanup prompt buttons.
- **Insight cards:** Flags awaiting cleanup, what's currently live in production,
  running experiment summary — each with an "Explore →" button.
