# Midjourney — Reference

Tools: `midjourney_imagine`, `midjourney_transform`, `midjourney_blend`,
`midjourney_with_reference`, `midjourney_edit`, `midjourney_describe`, `midjourney_shorten`,
`midjourney_translate`, `midjourney_generate_video`, `midjourney_extend_video`,
`midjourney_get_seed`, `midjourney_get_task`, `midjourney_get_tasks_batch`,
`midjourney_list_actions`, `midjourney_list_transform_actions`, `midjourney_get_prompt_guide`.

Midjourney is best for **stylized, artistic, editorial** output and has the richest set of
post-generation actions. As of 2026, **v8.1 is the default model**. Use `version: "8.1"`,
`mode: "fast"` unless told otherwise.

## Generate — `midjourney_imagine`

Returns a **2×2 grid (2048²)** plus an `image_id`, `task_id`, and an `actions` list. Set
`split_images: true` to get the 4 tiles separately. Other params: `mode` (fast/relax/turbo),
`quality` (.25/.5/1/2/4), `hd` (V8 4× cost), `moodboard`, `style_reference`, `translation`.

## Prompting style — tags + `--` parameters

Unlike Flux/Seedream, Midjourney **does** use comma-separated descriptors and `--flags`.
Order: `subject → action/pose → environment → composition/shot → style/medium → lighting →
mood → --params`. **Earlier words carry more weight** — front-load what matters.

### Parameter cheat-sheet
| Param | Range | Default | Notes |
|-------|-------|---------|-------|
| `--ar W:H` | any | 1:1 | Aspect ratio (16:9, 9:16, 4:5, 3:2, 21:9…). |
| `--v N` | 7/8/8.1 | 8.1 | Model version. |
| `--stylize` / `--s` | 0–1000 | 100 | Higher = more stylized, less literal. Keep low (50–150) for realism. |
| `--chaos` / `--c` | 0–100 | 0 | Variety across the 4 results. |
| `--weird` | 0–3000 | 0 | Offbeat aesthetics. |
| `--seed` | 0–4294967295 | random | Reproducibility. Get it via `midjourney_get_seed`. |
| `--no X` | text | — | Negative prompt (exclude X). |
| `--tile` | flag | off | Seamless tileable pattern. |
| `--iw N` | 0–3 (v7) | 1 | Image-prompt weight vs text (higher = closer to reference). |
| `--sref CODE/URL` | — | — | **Style** reference (aesthetic only, not subject). `--sw` 0–1000 sets strength. |
| `--oref URL` | — | — | **Omni/subject** reference (keep a character consistent), v7. `--ow` 0–1000. |
| `--raw` / `--style raw` | flag | off | Less house-style, more literal. Good for realism. |
| `--q` | 1/2/4 | 1 | v7 only (v8/8.1 use HD/SD instead). |

Note: some v7 params (`--oref`, `--q`, possibly `::` multi-prompt weights) are dropped in
v8/v8.1. When uncertain about a niche parameter, call `midjourney_get_prompt_guide`.

### Photorealism tips
Specify camera/lens/film ("shot on 85mm f/1.4, Kodak Portra 400"), real lighting, and add
`--style raw` with a low `--s`. High `--s` pushes an illustrative look.

### Distinctions between the image tools
- **image-as-prompt** (URL inside the imagine prompt) = influence content + style of this gen.
- **`--sref`** = borrow *style only*.
- **`--oref`** = keep a *subject/character* consistent.
- **`midjourney_blend`** = fuse 2–5 images (no text-as-tags needed).
- **`midjourney_describe`** = extract 4 candidate prompts *from* an image (reverse prompt).

## Transform — `midjourney_transform(image_id, action)`

Needs the `image_id` from a previous generation. Actions:
- From the grid: `upscale1`–`upscale4`, `variation1`–`variation4`, `reroll`.
- `variation_region` (inpaint) needs a base64 `mask` (white = regenerate).
- `zoom_out_2x`, `zoom_out_1_5x`, `pan_left/right/up/down` operate on an upscaled image.

⚠️ **`upscale_2x` and `upscale_4x` are NOT usable on v8.1** (verified): they return
`bad_request: "action not supported"`. A v8.1 upscaled image only exposes `upscale_subtle` /
`upscale_creative`, and those aren't in the `midjourney_transform` enum — so there is no
further-upscale path here. Treat a single `upscale<N>` (≈1456×816) as the final deliverable;
don't chain upscales.

Typical flow: `imagine` → choose a tile → `upscale<N>`. (Then optionally `zoom_out`/`pan`.)

### Picking a tile visually
`imagine` returns 4 candidates in one grid (and `sub_image_urls` when `split_images: true`).
Download the tiles/grid and **view them with the Read tool** (you're multimodal) to choose the
best, and/or render the clickable picker via `scripts/imgwidget.py picker` so the user can
choose. See SKILL.md → "Default Midjourney workflow" and "Showing generated images inline".

## Blend / reference / edit

- **`midjourney_blend(image_urls=[2–5], prompt)`** — merge multiple images. ✓ works with
  arbitrary URLs.
- **`midjourney_with_reference(reference_image_url, prompt)`** — re-imagine an external image;
  use `--iw 0–2` in the prompt to control influence. ✓ works with arbitrary URLs.
- **`midjourney_edit(image_url, prompt[, mask])`** — ⚠️ requires a **Midjourney-hosted/approved**
  image. An arbitrary URL fails with *"Prompt parameter error or image not approved."* For
  external images, use `with_reference` or `blend` instead; for your own MJ generations,
  prefer `transform`.

## Utility tools (instant, no polling)

- `midjourney_describe(image_url)` → 4 reverse-engineered prompts (last entry may be empty).
- `midjourney_shorten(prompt)` → up to 5 trimmed candidate prompts (good for long prompts).
- `midjourney_translate(content)` → Chinese → English prompt.
- `midjourney_get_seed(image_id)` → seed for reproducibility.
- `midjourney_get_prompt_guide` / `list_actions` / `list_transform_actions` → built-in docs.

## Image-to-video

- **`midjourney_generate_video(image_url, prompt, resolution="480p"|"720p")`** —
  **image-to-video only**, a reference image is required (no text-to-video). Optional
  `end_image_url`, `loop`. Returns 4 video variations + a `video_id`.
- **`midjourney_extend_video(video_id, prompt[, video_index])`** — lengthen a clip.
- Video costs far more credits than images and is the first thing to hit a low balance.

## Common mistakes

- Spaces inside `--ar` (`16:9`, not `16 : 9`).
- Mixing v7-only params (`--oref`, `--q`) into a v8.1 job.
- Expecting `--sref` to copy a subject (it copies style only — use `--oref`).
- Calling `midjourney_edit` with a non-Midjourney image URL (use `with_reference`/`blend`).
- Forgetting `midjourney_transform` needs an `image_id`, not a URL.
