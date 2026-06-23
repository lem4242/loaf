---
name: d3r-design-images
description: >-
  Generate, edit, and transform images with the d3r design server's four AI
  image engines — Flux (Black Forest Labs), Seedream (ByteDance), Midjourney, and
  Gemini (Google / Nano Banana).
  Use this whenever the user wants to create or modify an image: "generate/make/draw
  an image", "create a logo / poster / product shot / illustration / artwork / concept
  art", "edit this image", "change the background", "add/remove X from this photo",
  "make a watercolor/anime version", "upscale", "make variations", "blend these
  images", "style transfer", "image-to-video / animate this image", or any mention
  of Flux, Kontext, Seedream, SeedEdit, Doubao, Midjourney, Gemini, or Nano Banana.
  It picks the right
  engine and model, applies provider-specific prompting, and handles the
  submit→poll async workflow and the server's many parameter quirks. Reach for this
  even when the user doesn't name a tool — if they want a picture, use this skill.
metadata:
  author: d3r
  version: "1.1"
---

# d3r Design Server — AI Image Generation

Drive image generation through the **connected d3r design MCP tools** — do not hand-roll
HTTP/curl calls. This one MCP server exposes **four image engines**. In this plugin the
server is configured as `d3r-design`, so the tools appear as
`mcp__d3r-design__flux_generate_image`, `mcp__d3r-design__seedream_generate_image`,
`mcp__d3r-design__midjourney_imagine`, etc.; this skill refers to them by their short name
(`flux_generate_image`). If the server is registered under a different id in some install,
match on the **suffix**, not the prefix. If no d3r design MCP is connected, say so rather
than falling back to raw API calls.

| Engine | Provider | Strengths |
|--------|----------|-----------|
| **Flux** | Black Forest Labs | Literal prompt adherence, English in-image text, camera-grade photorealism, fast, clean editing (Kontext) |
| **Seedream** | ByteDance / Doubao | Bilingual **Chinese+English** text rendering, high native resolution (2K–4K), reference consistency, grouped/sequential sets |
| **Midjourney** | Midjourney | Stylized, artistic "wow-factor", editorial mood, rich post-actions (upscale/vary/pan/zoom), blend, image-to-video |
| **Gemini** | Google (Nano Banana) | Conversational, instruction-following edits; fast iterative changes; **synchronous** (no polling); accepts external image URLs (easy cross-engine edits) |

## The golden rule: everything is async — submit, then poll

Generation/editing tools return a **`task_id` immediately**, not an image. You must poll
the matching `*_get_task` (or `*_get_tasks_batch`) until the task reaches a terminal
state, then read the image URL from the result.

1. Call e.g. `flux_generate_image(...)` → get `task_id`.
2. Wait ~15–30s, then call `flux_get_task(task_id)`.
3. Repeat until done. Flux/Seedream finish in ~20–30s; Midjourney imagine ~60s.

**⚠️ Critical polling bug — do not trust `mcp_task_polling` to detect failure.**
On this server a *failed* task still reports `is_failed: false` and
`recommended_action: "poll"`. The real status is in the **`response`** object:
- Success → `response.success: true` and `response.data[].image_url` (Flux/Seedream)
  or `response.image_url` / `response.raw_image_url` (Midjourney).
- Failure → `response.success: false` and `response.error.message`.

So: **check `response.success` / `response.error` yourself.** If `response` is absent,
it's genuinely still running — keep polling. Don't blindly poll 100× on a dead task.

When waiting between polls, prefer a single background `sleep` rather than many short
foreground waits.

**Exception — Gemini is synchronous.** The Gemini tools (`gemini_generate_image`,
`gemini_edit_image`, `gemini_save_to_r2`) return the result **immediately** — a small inline
thumbnail plus, when R2 is configured, a full-res download URL — with **no `task_id` and
nothing to poll**. The submit→poll rule above applies only to Flux/Seedream/Midjourney.

## Choosing an engine

- **Photoreal scene, accurate English text in image, precise prompt following, speed** → **Flux** (`flux-2-pro`).
- **Chinese text (or mixed CN/EN) in image, very high resolution, a set of related images, brand/character consistency from references** → **Seedream** (`doubao-seedream-5-0-260128`).
- **Artistic / stylized / editorial look, or you need post-actions (upscale, variations, pan, zoom, blend) or image-to-video** → **Midjourney** (v8.1).
- **Editing an existing image** → Flux `flux_edit_image` (Kontext) is the most reliable on this server. See editing section. For **fast/conversational edits or editing an image from another engine**, **Gemini `gemini_edit_image`** is excellent and accepts an arbitrary external URL.
- **Fast iterative / conversational edits, strong instruction-following, or you want the result instantly (no polling)** → **Gemini** (`gemini_generate_image` / `gemini_edit_image`).

If the user is indifferent, default to **Flux `flux-2-pro`** (fast, cheap, faithful).
Offer to run the same prompt through 2–3 engines for comparison when the look matters.

## Per-engine quick reference (verified on this server)

Read the matching reference file in `references/` before writing prompts — each provider
wants a *different* prompt style. Below is the operational cheat-sheet.

### Flux — `flux_generate_image`, `flux_edit_image`
- **Models accepted:** `flux-dev`, `flux-pro`, `flux-kontext-pro`, `flux-kontext-max`,
  `flux-2-flex`, `flux-2-pro`, `flux-2-max`. (The `flux_list_models` text is **stale** —
  it lists `flux-pro-1.1` / `-ultra`, which the API rejects. Ignore it; use this list.)
- **Size depends on model:**
  - `flux-dev` / `flux-pro` → **pixel** dimensions, `WIDTHxHEIGHT`, 256–1440, multiples of 32 (e.g. `1024x1024`).
  - `flux-2-*` and `flux-kontext-*` → **aspect ratios only**: `1:1, 16:9, 4:3, 3:2, 21:9, 2:3, 3:4, 9:16, 9:21`. Pixel sizes are rejected.
- **Editing:** use `flux-kontext-pro` (or `-max`). `size` is **required** for
  `flux_edit_image` even though the schema marks it optional — always pass an aspect ratio.
- Prompt style: **natural-language sentences**, no `--flags`, no negative prompts. See `references/flux.md`.

### Seedream — `seedream_generate_image`, `seedream_edit_image`
- **Models:** `doubao-seedream-5-0-260128` (flagship, web-search), `-4-5`, `-4-0`,
  `doubao-seedream-3-0-t2i-250415` (seed + guidance_scale).
- **Size: `1K` is REJECTED by the backend** despite being the enum default. Use
  **`2K`, `3K`, `4K`, or `adaptive`**. Custom `WIDTHxHEIGHT` strings are rejected at the
  schema layer — stick to the presets. (`2K` returns ~2848×1600.)
- **Editing caveat:** the documented edit model `doubao-seededit-3-0-i2i-250628` returned
  *"does not exist or you do not have access"* on this account. If edits are needed, try a
  `doubao-seedream-4-x` model with an `image` input, or fall back to Flux Kontext.
- Prompt style: descriptive sentences, **quote literal text** to render, supports Chinese. See `references/seedream.md`.

### Midjourney — `midjourney_imagine` + friends
- `midjourney_imagine` → a 2×2 grid (2048²). Returns `image_id`, `task_id`, and `actions`.
  Use `version: "8.1"`, `mode: "fast"` by default.
- Prompt style: **comma-separated tags + `--` parameters** (`--ar`, `--stylize`, `--no`,
  `--style raw`, `--iw`, `--sref`). The other engines do NOT use this syntax. See `references/midjourney.md`.
- Post-actions: `midjourney_transform` (needs the `image_id`): `upscale1-4`, `variation1-4`,
  `zoom_out_2x/1_5x`, `pan_*`, `reroll`. **Do NOT chain `upscale_2x`/`upscale_4x`** — on v8.1
  they return `bad_request: action not supported` (a v8.1 upscaled image only exposes
  subtle/creative upscales, which aren't in the enum). One `upscale<N>` is the final deliverable.
- Also: `midjourney_blend` (2–5 image URLs), `midjourney_with_reference` (reference image +
  prompt), `midjourney_describe` (image → 4 prompts), `midjourney_shorten`,
  `midjourney_translate`, `midjourney_get_seed`.
- **Timing:** `imagine` takes ~60s (up to ~2min with `split_images`). The first poll/submit on
  any of these tools occasionally times out — just retry once; it's not a real failure.

### Gemini — `gemini_generate_image`, `gemini_edit_image`, `gemini_save_to_r2`
- **Synchronous** — returns the image inline at once (thumbnail + a `Full-res download:` R2 URL
  when configured). **No `task_id`, no polling.**
- **Quality:** `fast` = `gemini-3.1-flash-image` (cheaper, JPG); `high` = `gemini-3-pro-image`
  (best). `high` can transiently return **503 "high demand"** — retry shortly; it's a Google
  capacity blip, not a config error.
- **Size/ratio:** `aspect_ratio` (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`) and `image_size`
  (`512`/`1K`/`2K`/`4K`). Unlike Seedream, **`1K` is accepted**.
- **Editing is the strength:** `gemini_edit_image(prompt, image_url=…)` accepts an **arbitrary
  external URL** (including an AceData Flux/Seedream/Midjourney result), so it's the easiest way
  to do a cross-engine edit. Also takes `image_base64`. One change per call; name subjects
  explicitly (same discipline as Flux Kontext).
- **Needs a valid Google Gemini API key** on the server. If it's missing/stale you'll get
  `400 API_KEY_INVALID` straight from Google — a server env fix (redeploy), not something to
  retry. (`gemini_save_to_r2` does **not** need this key — see "Persisting to R2".)
- Prompt style: plain natural-language instructions. See `references/gemini.md`.

### Default Midjourney workflow — let the user pick visually

Midjourney always returns 4 candidates; you can't ask for one. Turn that into a feature:

1. `midjourney_imagine(..., split_images: true)` → grid + `image_id` + 4 `sub_image_urls`.
2. Download the 4 tiles (or the grid) and **view them with the Read tool** — you're multimodal,
   so actually look and judge which is strongest. State your recommendation.
3. Render a **clickable picker** so the user can choose: run
   `scripts/imgwidget.py picker --grid-url <raw_image_url> --image-id <id> --desc1.. --desc4..`,
   then Read the written HTML file and pass it as `widget_code` to `mcp__visualize__show_widget`.
   Clicking a quadrant sends back an upscale instruction for that tile.
4. On the user's pick (or your recommendation if they say "you choose"), run
   `midjourney_transform(image_id, "upscale<N>")` and deliver the single final image (see below).

## Editing, transforming & combining images

- **Flux edit (most reliable):** `flux_edit_image(prompt, image_url, model="flux-kontext-pro", size="1:1")`.
  Write edits as *action + what to preserve* ("Add falling snow; keep the fox and composition unchanged").
  Name subjects explicitly, never "it/this". Iterate one change at a time.
- **Seedream edit:** `seedream_edit_image(prompt, image=[url], ...)` — short imperative instruction,
  one change per call. Subject to the access caveat above.
- **Midjourney edit:** `midjourney_edit` requires a Midjourney-hosted/approved image — passing an
  arbitrary URL fails with *"Prompt parameter error or image not approved."* Prefer
  `midjourney_transform` on an `image_id` you generated, or `midjourney_with_reference` for
  re-imagining an external image.
- **Gemini edit (best for cross-engine + conversational edits):** `gemini_edit_image(prompt, image_url=<any URL>)`
  fetches the source server-side — **arbitrary external URLs work**, including AceData
  Flux/Seedream/Midjourney results — applies the change, and returns the edited image inline + an
  R2 URL. Synchronous (no polling). Also accepts `image_base64`. One change per call; name
  subjects explicitly. (Verified: editing a Midjourney result with Gemini works end-to-end.)
- **Blend:** `midjourney_blend(image_urls=[2–5 urls], prompt=...)`.
- **Reuse outputs:** the `image_url` from one engine can be fed as input to another engine's
  edit/blend/reference tool.

## Persisting to R2 (permanent, owned links)

Flux/Seedream/Midjourney return images on AceData's CDN (`*.cdn.acedata.cloud`), which may be
**temporary**. To get a durable, owned link, pass that URL to **`gemini_save_to_r2`**:

- `gemini_save_to_r2(image_url=<acedata or any URL>)` → fetches the image server-side, stores it
  in the Cloudflare R2 bucket, and returns `Saved <bytes> to R2. Download: <url>` plus a
  thumbnail. It also accepts `image_base64`.
- The returned link is on the **configured R2 public domain** — on this install
  `https://ai-images.vivelia.co/gemini-image/<id>.<ext>` (**not** a `pub-<hash>.r2.dev` URL; the
  bucket is mapped to a custom domain). Don't assume the `r2.dev` form.
- **Independent of the Gemini API key** — `gemini_save_to_r2` only fetches + stores, so it works
  even when `gemini_generate_image`/`gemini_edit_image` are failing on an invalid Gemini key. It
  needs the `R2_*` env set; if not, it returns a clear "R2 is not configured" error (an
  Obot/Dokploy env fix, not a code issue).
- **Gemini generate/edit already return an R2 URL inline** when R2 is configured, so they don't
  need a separate save step — only the AceData engines do.

**Default post-generation step:** after a Flux/Seedream/Midjourney result the user wants to keep,
run `gemini_save_to_r2` on its `image_url` and give them the R2 link as the durable copy
(alongside the original CDN URL).

## Image-to-video (Midjourney)

`midjourney_generate_video(image_url, prompt, resolution)` is **image-to-video only** — a
reference image is required (no pure text-to-video). `midjourney_extend_video(video_id, ...)`
lengthens an existing clip. Both consume significantly more credits than images.

## Showing generated images inline in chat

Generated images live on the `acedata.cloud` CDN. Two things to know:

- **A plain `<img src="https://...acedata...">` inside a `mcp__visualize__show_widget` widget
  will NOT render** — the widget sandbox enforces a CDN allowlist and acedata isn't on it, so
  the image silently breaks. To show an image in a widget you must **embed the bytes** as a
  base64 data URI.
- Embedding is token-expensive, so **downscale hard first**. Use `scripts/imgwidget.py`, which
  downloads, downscales, base64-encodes, and writes ready-to-use widget HTML to a file. Then
  Read that file and pass its contents as `widget_code`. (The tool needs the literal HTML
  inline — there's no way to point it at a file, so small widths matter.)
  - `imgwidget.py single --url <image_url> --alt "..."` → embed one image for display
    (use ~440px width; the file/CDN URL still holds the full-res original).
  - `imgwidget.py picker --grid-url <url> --image-id <id> ...` → the Midjourney chooser above
    (use ~300px — it's only for picking; the upscale is full-res).

Always also give the user the **direct CDN URL** in your text (markdown link) so they can open
the full-resolution original — the embedded widget copy is a downscaled preview.

For Flux/Seedream single results, the same `imgwidget.py single` approach displays them inline.

## Account balance

These tools draw on a shared Ace Data Cloud balance. A request can fail with *"Your balance
is not sufficient…"* — this is an **account issue, not a code error**. Video and some
higher-cost models are the first to hit it. If you see it, stop retrying and tell the user
they need to top up at the Ace Data Cloud platform.

## Reference files & scripts

- `references/flux.md` — Flux/Kontext/FLUX.2 models, natural-language prompting, editing, params.
- `references/seedream.md` — Seedream/SeedEdit versions, bilingual + text-in-image prompting, params.
- `references/midjourney.md` — Midjourney v7/v8/v8.1 prompt structure, full `--` parameter list, references, actions.
- `references/gemini.md` — Gemini (Nano Banana) synchronous generate/edit, quality tiers, params, cross-engine editing, and R2 notes.
- `scripts/imgwidget.py` — builds embeddable `show_widget` HTML for a clickable Midjourney
  picker (`picker`) or a single inline image (`single`). Run it, then Read the output file and
  pass its contents as `widget_code`. See "Showing generated images inline in chat".

Read the relevant one when crafting prompts — the three engines reward genuinely different
prompting styles, and getting that right matters more than any single parameter.
