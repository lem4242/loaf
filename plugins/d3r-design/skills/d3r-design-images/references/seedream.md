# Seedream (ByteDance / Doubao) — Reference

Tools: `seedream_generate_image`, `seedream_edit_image`, `seedream_get_task`,
`seedream_get_tasks_batch`, `seedream_list_models`, `seedream_list_sizes`.

Seedream's signature strengths: **bilingual Chinese+English text rendering**, **high native
resolution (2K–4K)**, strong reference consistency, and **grouped/sequential** image sets.

## Models

| Slug | Type | Notes |
|------|------|-------|
| `doubao-seedream-5-0-260128` | T2I | **Flagship.** Highest quality; deep reasoning; optional `web_search` grounding; sequential/streaming. **Default pick.** |
| `doubao-seedream-4-5-251128` | T2I | Previous flagship; excellent text rendering; sequential/streaming. |
| `doubao-seedream-4-0-250828` | T2I | Stable, best value; sequential/streaming. Can also edit with `image` input. |
| `doubao-seedream-3-0-t2i-250415` | T2I | Supports **`seed`** and **`guidance_scale`** for reproducibility/control. |
| `doubao-seededit-3-0-i2i-250628` | Edit (i2i) | Dedicated editor — **but returned "does not exist / no access" on this account.** See caveat. |

## Size rules (verified — important)

- The enum is `1K / 2K / 3K / 4K / adaptive`, but **`1K` is REJECTED by the backend**
  ("size must be one of 'WIDTHxHEIGHT', '2k', '3k', or '4k'"). **Use `2K`, `3K`, `4K`, or
  `adaptive`.**
- Despite the backend message, **custom `WIDTHxHEIGHT` strings are rejected at the schema
  layer** — only the presets pass. Stick to `2K`/`3K`/`4K`/`adaptive`.
- `2K` produced ~2848×1600. Use `adaptive` to let the model choose the aspect ratio.

## Prompting style — descriptive sentences

Like Flux, Seedream wants **natural-language description**, not keyword tags. Brief it like a
photographer.

- Structure: `[Subject] + [Action/Pose] + [Setting] + [Style] + [Lighting/Atmosphere] +
  [Technical specs] + [Text content]`.
- **Length sweet spot ≈ 30–100 words / 2–4 sentences.** Under ~15 words leaves too much to
  chance; over ~150 words instructions start conflicting. v5.0's reasoning rewards more detail.
- **Word order matters** — lead with the most important subject/detail.
- **Bilingual:** prompts work in Chinese or English; Chinese typography is a deliberate strength.

### Text-in-image (a top strength)
- Put literal text in **double quotes**; accuracy drops sharply without quotes.
- Keep rendered text short (~3–5 words) and specify font/placement ("bold sans-serif, white,
  centered at top").
- Render at **2K/4K** for crisp small text.

### Styles
Name a **medium + aesthetic**: "editorial photography, studio lighting, 85mm, sharp focus"
for realism; "oil painting, impressionist brushwork" / "cyberpunk neon" for stylized. Style
blending works ("cyberpunk city in impressionist style").

## Key features / parameters

- **`guidance_scale`** (v3 only): higher = stricter prompt adherence; lower = more creative.
  Defaults: **2.5** for `-3-0-t2i`, **5.5** for the i2i editor. Range 1–10. (Newer models don't
  expose it.)
- **`seed`** (v3 only): fix for reproducibility, vary for new results.
- **`sequential_image_generation: "auto"`** + `sequential_image_generation_options.max_images`
  (1–15) on v4.0/v4.5 → a cohesive set/series (campaigns, storyboards, variations).
- **`tools: ["web_search"]`** on v5.0 only → ground the image in live info; leave off for purely
  imaginative prompts.
- `stream`, `optimize_prompt_options` (v4.0/4.5), `watermark` (default true → set false to
  remove), `response_format` (`url` default / `b64_json`), `output_format` (`jpeg`/`png`).
- Async: completes in ~20–30s.

## Editing (`seedream_edit_image`)

- Pass `image=[url_or_base64, ...]` (each <10MB) + a **short imperative instruction**.
- **Caveat:** the default edit model `doubao-seededit-3-0-i2i-250628` was inaccessible on this
  account ("does not exist or you do not have access"). If you must edit with Seedream, try
  `model="doubao-seedream-4-0-250828"` with an `image` input. Otherwise prefer **Flux Kontext**.
- Edit one change per call and iterate; stacking many edits in one instruction degrades results.
- Works well: portrait retouching with face preservation, background/scene/lighting changes,
  object add/remove, attribute edits, text replacement (`Change 'STOP' to 'WARM'`), style
  transfer. Multi-image composition / virtual try-on are best on a v4.x model (multi-reference).

## Common mistakes

- Using `size: "1K"` (rejected) or a custom `WIDTHxHEIGHT` (rejected) — use `2K`/`3K`/`4K`/`adaptive`.
- Comma-separated keyword dumps; over-long or contradictory prompts.
- Forgetting to quote literal text, or rendering text at low resolution.
- Expecting the dedicated i2i edit model to work without access.
