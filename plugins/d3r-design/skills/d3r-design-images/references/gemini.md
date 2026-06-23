# Gemini (Google — "Nano Banana") — Reference

Tools: `gemini_generate_image`, `gemini_edit_image`, `gemini_save_to_r2`.
Provided by the custom `gemini-image-mcp` server bundled into the d3r design connector
(distinct from the AceData engines Flux/Seedream/Midjourney).

## What makes Gemini different

- **Synchronous.** Generate/edit return the image **immediately** — there is no `task_id`
  and nothing to poll. This is the exception to the skill's submit→poll "golden rule".
- **Output shape:** the result text reads
  `Image created with <model> (<bytes>). Full-res download: <url>` plus a small inline JPEG
  thumbnail (~3–15 KB) preview. The thumbnail is just a preview; the **R2 URL is the real
  full-res file** — give the user that link.
- **Strong at editing**, multi-turn/conversational refinement, and precise instruction
  following. Reach for Gemini for quick iterative edits and cross-engine edits.

## Models / quality

| `quality` | Model | Notes |
|-----------|-------|-------|
| `fast` (default) | `gemini-3.1-flash-image` | Cheaper, quick, JPG output. Great for iteration. |
| `high` | `gemini-3-pro-image` | Best quality. Can transiently return **503 "high demand"** — retry shortly; a Google capacity blip, not a config error. |

## Parameters

- `prompt` (required) — natural-language description (generate) or instruction (edit).
- `quality` — `fast` / `high` (see above).
- `aspect_ratio` — e.g. `1:1`, `16:9`, `9:16`, `4:3`, `3:4`.
- `image_size` — `512`, `1K`, `2K`, `4K`. **Unlike Seedream, `1K` is accepted.**
- (edit only) `image_url` **or** `image_base64` — the source image.

## Editing (`gemini_edit_image`)

- Pass the source as `image_url` (fetched server-side) **or** `image_base64`.
- **External URLs work** — including AceData Flux/Seedream/Midjourney result URLs — so Gemini
  is the easiest way to do a **cross-engine edit** (generate in another engine, refine in Gemini).
- Write edits as **action + what to preserve**, one change per call; name subjects explicitly
  (never "it"/"this"), same discipline as Flux Kontext. Example:
  *"Add a red knitted scarf around the pig's neck. Keep the pig, the meadow, and the
  composition unchanged."*
- Returns the edited image inline + an R2 full-res URL (when R2 is configured).

## Persisting / R2 — `gemini_save_to_r2`

- `gemini_save_to_r2(image_url=<any URL>)` (or `image_base64=…`) fetches the image and stores
  it in the Cloudflare R2 bucket, returning `Saved <bytes> to R2. Download: <url>`.
- Use it to give **AceData (Flux/Seedream/Midjourney)** results — whose CDN links may expire —
  a permanent, owned link. Gemini's own generate/edit already return an R2 URL inline when R2
  is configured, so they don't need a separate save step.
- The link is on the **configured R2 public domain** — e.g. on this install
  `https://ai-images.vivelia.co/gemini-image/<id>.<ext>`, **not** a `pub-<hash>.r2.dev` URL.
  Don't assume the `r2.dev` form.
- **Independent of the Gemini API key** — it only fetches + stores, so it works even when
  `gemini_generate_image`/`gemini_edit_image` are failing on a bad key.

## Failure modes (server config — not retryable in-tool)

- `400 INVALID_ARGUMENT … API key not valid (API_KEY_INVALID)` — the **Google Gemini API key**
  on the server is missing/stale/wrong (the error comes straight from Google). Fix the
  `GEMINI_API_KEY` env on the `gemini-image-mcp` container (a valid AI Studio / Generative
  Language key) and **redeploy** — a plain restart may not reload changed env, and the connector
  drops and needs reconnecting in Obot. Don't keep retrying; it won't self-heal.
- `R2 is not configured` (from `gemini_save_to_r2`, or no "Full-res download" line on
  generate/edit) — the `R2_*` env isn't set on the container. Same redeploy caveat.
- `503 UNAVAILABLE … high demand` — transient Google capacity (mostly `high`/pro). Retry shortly.

## Prompt style

Plain natural-language sentences (like Flux, unlike Midjourney's tag + `--flag` syntax). State
what you want; for edits, state the change and what to preserve.
