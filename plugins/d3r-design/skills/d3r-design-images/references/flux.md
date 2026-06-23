# Flux (Black Forest Labs) — Reference

Tools: `flux_generate_image`, `flux_edit_image`, `flux_get_task`, `flux_get_tasks_batch`,
`flux_list_models`, `flux_list_actions`.

## Models (use these exact slugs — verified on the server)

`flux_list_models` output is **stale** (it advertises `flux-pro-1.1`, `flux-pro-1.1-ultra`,
which the API rejects). The actually-accepted models are:

| Slug | Use | Notes |
|------|-----|-------|
| `flux-dev` | T2I | Open 12B baseline, cheap, fast, lower fidelity. Pixel sizes. |
| `flux-pro` | T2I | Stronger production baseline. Pixel sizes. |
| `flux-kontext-pro` | **Editing** (+T2I) | Instruction editing, character consistency, iterative edits. Aspect ratios. ~1MP cap. |
| `flux-kontext-max` | **Editing** (+T2I) | Highest Kontext quality, better prompt adherence/typography. Aspect ratios. |
| `flux-2-flex` | T2I + edit | Exposes finer control; good for typography. Aspect ratios. |
| `flux-2-pro` | T2I + edit | **Default pick.** Strong quality, low cost, up to 8 references. Aspect ratios. |
| `flux-2-max` | T2I + edit | Max quality + real-world grounding search. Aspect ratios. |

Default to **`flux-2-pro`** for generation, **`flux-kontext-pro`** for editing.

## Size rules (verified)

- `flux-dev` / `flux-pro`: **pixel** `WIDTHxHEIGHT`, 256–1440px, multiples of 32. E.g.
  `1024x1024`, `1344x768`, `768x1344`.
- `flux-2-*` and `flux-kontext-*`: **aspect ratios only** — `1:1, 16:9, 4:3, 3:2, 21:9,
  2:3, 3:4, 9:16, 9:21`. Passing pixel dimensions errors out.
- `flux_edit_image` **requires** `size` even though the schema says it's optional. Always
  pass an aspect ratio (e.g. `1:1`) or the call fails with "size is required".

## Prompting style — natural language, not tags

Flux is the opposite of Midjourney. Write **descriptive sentences / scene narration**, not
comma-separated keyword soup, and **no `--flags`**.

- Optional structure: `[subject], [setting], [style], [camera/lens], [lighting], [colors], [extra elements]`.
- **Photorealism:** describe camera, lens, film, lighting, materials in prose — e.g.
  "shot on 85mm f/1.4, soft window light, shallow depth of field, Kodak Portra 400".
- **Typography:** put exact words in **double quotes** to render them; FLUX.2 is excellent at
  clean lettering (ads, UI mockups, infographics). For edits: `Replace 'OLD' with 'NEW'`.
- **Exact colors:** FLUX.2 honors hex codes (e.g. `#02eb3c`) for brand work.
- **No negative prompts** — state what you *want*, not what to exclude.
- **Language:** multilingual but English is most precise.
- Short prompts get auto-upsampled on flux-2-pro/max/flex; still, more detail = more control.

## Editing with Kontext (`flux_edit_image`)

Three-layer instruction: **Action** (what to change) + **Context** (how it relates) +
**Preservation** (what must stay the same).

- Be specific. **Name subjects directly** ("the woman with short black hair", "the red car") —
  never pronouns ("her", "it", "this").
- Explicitly state what to preserve to protect identity, pose, framing, lighting:
  "Change the car to red **while keeping the same body shape, background and lighting**."
- Edits that work well: color/attribute changes, add/remove objects, background/weather/lighting
  changes, style transfer, and **text editing** (`Replace 'X' with 'Y'`).
- **Iterate** — make one change per call and build up; dramatic transforms should be split into
  several sequential edits. Identity can drift and artifacts can appear after ~6 chained edits.
- Output caps near **1MP** on Kontext; FLUX.2 editing goes higher.

## FLUX.2 multi-reference

FLUX.2 models accept multiple reference images (API up to 8). In the prompt, refer to inputs as
**"image 1", "image 2"** and describe each one's role (which character/product/style to take
from where). Use for character consistency, product placement, style transfer, compositing.

## Parameters / behavior

- `count` — number of images (generate only).
- `callback_url` — optional webhook; otherwise poll `flux_get_task`.
- Result image URLs are CDN links (e.g. `…/flux/<task_id>.jpg|png`).
- Async: typically completes in ~15–25s.

## Common mistakes

- Writing Midjourney-style tag lists or `--ar`/`--stylize` flags (Flux ignores them — bake
  aspect ratio into `size` instead).
- Using a pixel size with a `flux-2-*`/kontext model, or forgetting `size` on an edit.
- Relying on negative prompts.
- Using pronouns in edit instructions, or stacking many edits into one instruction.
