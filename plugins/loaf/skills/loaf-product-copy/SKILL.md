---
name: loaf-product-copy
description: >-
  Find Loaf products with missing or weak PDP copy and work through them one at a
  time, drafting on-brand product_description, feature_bullets and one_line_summary
  against a live best-seller benchmark, then saving approved copy back to the DB via
  update_product. Use when someone says "fix product copy", "find products missing
  descriptions", "write descriptions for the gaps", "copy audit", or wants to fill
  empty PDP copy. Prioritises by commercial impact (category sales weight). Pulls a
  best-seller reference set first so new copy matches house voice and length.
  Connectors: loaf (sales/catalogue).
---

# Loaf Product Copy — Gap Finder & Writer

A guided, human-in-the-loop workflow. Claude finds the gaps, prioritises them, and
for each product shows the current state + image + a quality assessment vs the
benchmark, drafts new copy, and only writes back after Lynton approves.

The loaf connector is read-mostly: `get_products` reads, `update_product` writes.
There is no server-side text search, range filter, or aggregation — filters are
exact-match `[field, value]` tuples (value may be an array = OR). Plan around that.

## Step 0 — Open with a SUMMARY dashboard (the first screen, always)

Before gathering reference copy or working any product, run the gap searches +
cruft ruleset + dedupe silently, then present a one-screen summary so Lynton can
choose where to start. Render KPI cards (a `show_widget` mockup is on-brand) plus a
prioritised category table in the chat. The summary should report:

* **Universe:** active products (~610) vs the non-live pile excluded by status
  (archived ~2.5k, inactive ~3k, no-web-stock ~170, posoms ~92).
* **In-scope:** candidates after structural cruft (type 0 ~114, covers ~25 removed).
* **Genuine gaps:** real PDPs missing description/bullets AFTER dedupe — and how many
  were dropped as duplicate shells (finish/leg/Early-Edition twins).
* **One-liner caveat:** `one_line_summary` is empty catalogue-wide (~590), incl. best
  sellers — flag as a single org-wide decision, NOT ~590 individual gaps.
* **Priority order:** genuine gaps grouped by category, ranked by category sales
  weight (sofas → footstools → headboards → … → homewares).

End the summary by asking which slice to start on (a category, a model, or top-N).
THEN proceed to Step 0b (reference) for the chosen scope.

## Step 0b — Build the best-seller reference set (before drafting any copy)

The benchmark for voice + length comes from live best sellers, NOT from a guess.

```
get_products
  filters: [["status","active"], ["best_seller","true"]]
  only_fields: ["id","title","type","product_description","feature_bullets"]
  sort: [["position","ASC"]]
  limit: 22
```

`best_seller=true` is the efficient signal — it returns the hero products across
every category (Crumpet/Jonesy/Squishmeister Sofas, Our Perfect Mattress, Milk
Stool, Young Flapper Chest, etc.). `position` alone is unreliable (mostly 0/unset).

⚠️ The `best_seller` flag sometimes sits on an EMPTY duplicate shell (e.g. an "Early
Edition – X" record) rather than the populated canonical. So only use records with a
non-empty `product_description` as exemplars — discard the blanks the filter returns
rather than treating them as "best sellers with no copy".

If a category in the worklist has no best-seller exemplar, top up with 2–3 from that
type, e.g. `filters:[["status","active"],["type","109"]]` and read their copy.

### House style derived from the reference set (use as the guide)

* **product_description:** 1–3 sentences, witty/warm Loaf voice, ~15–50 words (sweet
  spot ~25–40). Often a one-line quip to finish ("Bagsie that.", "Living the gleam!",
  "Go on, take it for a spin.", "Brilliant."). Plain text (the DB also stores an HTML
  twin in `body`).
* **feature_bullets:** 2–5 short benefit phrases, 2–6 words each, Title case, NO full
  stops ("Solid oak legs", "Deep feather-wrapped seat cushions", "Shorter back legs
  for a more comfortable sit").
* **one_line_summary:** ⚠️ empty across the whole catalogue — even on best sellers.
  There is no in-DB benchmark. Decide with the user: skip it, or establish a
  convention in the "Why we love our X" voice from the PDP (~12–18 words, one
  benefit-led sentence). Don't silently invent it.

## Step 1 — Find the gaps (the searches)

Empty-string exact match works for finding blanks. Run against active products.

* No description: `filters:[["status","active"],["product_description",""]]`
* No one-liner: `filters:[["status","active"],["one_line_summary",""]]`
* No copy at all: `filters:[["status","active"],["product_description",""],["one_line_summary",""]]`

Pull `only_fields:["id","title","type","urlname"]` (full descriptions overflow the
context — never pull `product_description` across the whole set; fetch per product).

### Cruft / ignore ruleset (apply BEFORE prioritising)

Most blank records are not customer-facing PDPs. Drop them in two tiers.

**HARD excludes (safe to auto-skip):**

* `status != "active"` — known non-web states with real counts: `active` ~610 (the
  ENTIRE in-scope universe), `archived` ~2,500, `inactive` ~3,000, `no-web-stock`
  ~170, `posoms` ~92 (POS/OMS-only, almost all spares). ~94% of all records are
  non-live, so always filter `status="active"` first; default to active-only. Note on
  `posoms` (verified): these are POS/OMS-only spares & service items, not catalogue
  PDPs — overwhelmingly "Legs for <model>" replacement legs, plus fees/add-ons like
  "Storage Fee" and "Spare Room Zip & Link" (all type 0/1, no copy). Cruft for web PDP
  copy, BUT their titles appear in customer confirmation/order emails, so the names
  must stay sensible. Out of scope for this copy pass; don't treat the title as
  throwaway.
* `type == "0"` — uncategorised: frames, "Remove My"/"Take away" services, legs,
  supplies, date/campaign pages, range landing pages. (~114 of ~601 active.)
* cover types `179, 180, 181, 182` — loose/additional covers. (~25 of ~601 active.)
* `demo_product` is set — display dummies (e.g. a bed used to show bed linen).
* **No active stockitem** — the REAL liveness test. A product can be `status="active"`
  yet have zero active stockitems, meaning nothing is buyable, so it doesn't render on
  site or in search (confirmed: Bowie Coffee Table in Dark Oak 3841 — empty Stock
  Items, absent from search, yet "active"). There is NO product-level field for this;
  detect via stockitems. Efficient batch test: `get_stockitems` with
  `filters:[["product",[<ids>]],["status","active"]]`, `only_fields:["product"]` — any
  candidate id NOT returned has no live stockitem → drop it. Chunk ids ~100 at a time.
  Run this over the worklist before writing copy: a PDP for a product with no
  stockitem is wasted effort.

**SOFT flags (review, don't auto-delete — title keywords, case-insensitive):**

* `OLD ...` — retired duplicates (e.g. "OLD Jonesy", "OLD Squishmeister Sofa Bed").
* `Early Edition ...` — NOT cruft by keyword, but usually a DUPLICATE SHELL. The empty
  "Early Edition – X" record almost always has a populated canonical twin "X" (e.g.
  empty `Early Edition – Bed in a Bun` 1623 ↔ full-copy `Bed in a Bun` 5406). The
  `best_seller` flag often sits on the empty shell, not the populated canonical — so
  these look like high-value gaps but aren't. Resolve via the dedupe step below.
* `Castelan -` — furniture-protection variants.
* `... Frame`, `Flat-Pack(ed) ...` — frame/component records (most are already type 0).
* `Leg No.`, `CS Leg`, `Miscellaneous Parts`, `... Supplies`, `... family` —
  components and range/landing pages.
* `type == "1"` — the Furniture catch-all; usually a landing/cover record, verify.
  Keyword rules can false-positive (e.g. a real product legitimately saying "Frame"),
  so flag for a human glance rather than hard-dropping.

Net effect (last run): ~601 active → ~139 hard structural cruft → ~462 candidates,
then soft flags trim to the genuine PDP worklist. The earlier no-copy pass showed
~184 records with no copy → ~136 cruft, ~48 real PDPs; plus ~410 with a description
but no one-liner.

### Dedupe against canonical twins (do BEFORE treating a blank as a gap)

The catalogue holds duplicate records: a base product plus variant shells that are
often empty. An empty record with a populated twin is NOT a fresh-copy gap — its copy
should be inherited/synced from the twin, or the shell ignored.

* Normalise the title by lowercasing + collapsing whitespace, then stripping variant
  affixes: leading `Early Edition`, `OLD`, `NEW`, and trailing `- Metal Leg`, `in Dark
  Oak`/` in <finish>`, size words. Group records that share the normalised name. Case
  matters: `Top Of The Blocks` and `Top of the Blocks` are the SAME range (the casing
  variant is often an archived dup).
* Range voice lead = the active variant that already HAS good copy (often the Sofa),
  even if the gap you're filling is a different variant (e.g. the Footstool). Cascade
  the lead's voice down; don't invent a new voice per variant.
* If any record in the group has copy, the blanks are duplicates → inherit the twin's
  copy (adapted) or skip; do not count them as net-new gaps.
* Confirmed example: empty `Early Edition – Bed in a Bun` (1623, flagged best_seller)
  ↔ populated `Bed in a Bun` (5406). Same for Bed in a Button, Cuddlemuffin Chaise.
* Only when NO record in the group has copy is it a genuine gap.
* CONFIRMED finish/leg pattern: `… in Dark Oak` and `… - Metal Leg` records are almost
  always empty duplicates of a populated base whose copy already spans finishes ("Made
  from solid oak in light or dark…"). Verified dups incl. Bowie Coffee/Side Table,
  Bastille/Heyday Side Table, Elodie Chest, Bread Table, Bumble Stool, Jeffers
  Sofa/Footstool. ~9 of ~48 "gaps" were these → drop, don't write.

## Step 2 — Prioritise by commercial impact

Rank the real-PDP gaps by how much their category sells, so we fix money-makers
first. Cheap, "good-enough" signal (don't over-engineer — efficiency > analytical
purity):

1. Group the gap list by `type`.
2. Weight each type by recent sales. Either:
   * **quick:** trust the known order — Sofas/Standard sofa (109/6) ≫ Chaise (33) >
     Beds (16/4) > Footstools (110) > Headboards (59) > Rugs (136) > Side tables (103)
     > Coffee tables (37) > Kitchen tables/chairs > Cushions/Lighting > rest; or
   * **precise:** pull `get_product_type_sales` for a recent window (enumerate the
     dates in the filter — no range operator), aggregate value per type locally.
3. Within a type, do `best_seller=true` items first, then by `position`.

Produce an ordered worklist: id, title, type, category, url, gap
(desc/one-liner/both).

## Step 2.5 — Work in MODELS (families), not single products

Prefer to fix a whole model at once. A "model" is the named range — Sloafer, Crumpet,
Bruges, Jonesy — which is sold as variants: Sofa, Corner Sofa, Love Seat, Armchair,
Chaise, Footstool, Sofa Bed, plus loose Covers. The tone must be consistent across the
family, so agree the copy once on the lead product and cascade.

### Grouping is by title, not the range field

`range` / `group` / `group_title` are mostly empty (0) — do NOT rely on them. Group by
the leading model token of the title (the first word, e.g. "Sloafer"). Gather a family
by querying exact-title variants:

```
filters:[["title",["<Model> Sofa","<Model> Corner Sofa","<Model> Love Seat",
  "<Model> Armchair","<Model> Chaise Sofa","<Model> Footstool","<Model> Sofa Bed",
  "<Model> Sofa Cover","<Model> Corner Sofa Cover","<Model> Love Seat Cover",
  "<Model> Armchair Cover","<Model> Footstool Cover"]]]
```

then `only_fields:["id","title","type","status","best_seller","product_description",
"feature_bullets","one_line_summary"]`. (Models differ: some separate out
corners/armchairs as their own PDPs, some fold them into sizes within the Sofa. Some
variants are archived. Read what's actually there.)

### Cascade rules

1. Lead product = the active, highest-value variant (usually the Sofa, type 109). Agree
   `product_description` + `feature_bullets` + `one_line_summary` here with Lynton.
2. Cascade to siblings, adapting per variant (swap "sofa"→"footstool"/"armchair",
   adjust bullets for that variant's real features/dimensions). Keep the same voice,
   hook and bullet phrasing as the lead.
3. Apply to a sibling only where it's MISSING or WORSE than the lead/benchmark:
   * empty field → fill it;
   * existing copy that's off-voice, too short, or thinner than the lead → replace;
   * existing copy already as good as the lead → leave it (note it, don't churn).
4. Skip archived variants (`status != active`) — don't spend copy on retired PDPs.
5. Covers (types 179–182) are optional/light — confirm with Lynton whether they get
   copy at all before writing. Still write back one record at a time, each confirmed
   (see Step 4).

### Per-model flow (the loop Lynton wants)

1. Show the range card (all variants, status/copy/action).
2. Show the lead product you suggest starting with — full drafted card (Step 3), and
   get Lynton to AGREE the lead copy first (this sets the range voice).
3. Then agree the variants: cascade the agreed lead into each in-scope variant, present
   each as its own card, agree one at a time, and write each back on approval. Do not
   draft the variants until the lead is agreed — they inherit its voice.

### Range card (open every model with this)

Before drafting, show a "range card": the range name as a heading (`##`), a range link
(`https://loaf.com/search?q=<model>`) + lead PDP link, then a table of ALL variants:
`Variant | id | Type | Status | Copy | Action`. Action = Lead-write / Cascade-write /
Skip-cover / Skip-archived / Skip-no-stockitem. Footer: counts in-scope vs skipped.
This makes the cruft/dedupe/liveness decisions visible per range before any writing.
Layout: ALWAYS render the range card and the active product card together inside one
container (a single `show_widget`), stacked — range card on top, product card below,
with the Approve & save button on the product card (button rules per Step 4).

## Step 3 — Work each product (the loop)

For each product, in priority order:

1. **Load full context — one call:**

```
get_products filters:[["id", <id>]]
  only_fields:["id","title","type","urlname","product_description","product_tagline",
    "one_line_summary","feature_bullets","body","one_line_summary","dimensions",
    "features","meta_title","meta_description","listing_image"]
```

   Read everything already said about it (body, features, meta, dimensions) so the
   draft is accurate, not invented.
2. **Give Lynton a link + show the image.**
   * Primary link = the DB `urlname`: `https://loaf.com/products/<urlname>`. The
     `urlname` is the product's actual stored slug (not a guess), so this is exact and
     reliable. Fallback only = site search `https://loaf.com/search?q=<name>`.
   * ⚠️ Search index ≠ live catalogue. On-site search can return nothing for a product
     that is fully live (e.g. Outlet/sale lines like "Bowie Coffee Table" — PDP loads,
     in stock, indexed for Google, but absent from search). NEVER infer a product is
     retired from an empty search; confirm via the `/products/<urlname>` PDP.
   * Image: the product `listing_image` / Cylindo render is the hero, but external
     image origins (media.loaf.com, content.cylindo.com) are blocked by the widget
     CSP, so embed the image as a markdown image in the chat response, not in
     `show_widget`. Build the Cylindo URL from the stockitem's `cylindo_data` (`model`
     + `COLOUR`):
     `https://content.cylindo.com/api/v2/4980/products/<model>/frames/3/<sku>.png?size=(900,640)&feature=COLOUR:<id>`.
     If the product has no image set (some don't), don't fake one — just give the
     search link and say the image is missing.
   * The live PDP (`/products/<urlname>`) also reveals the public meta-description and
     "Why we love our X" line — useful raw material; note it's JS-rendered so
     `web_fetch` may return it without images.
3. **Assess current vs benchmark** — short, candid: which of description / bullets /
   one-liner exist, are they on-voice, right length? Score the gap and say what's
   missing relative to the Step-0 style guide.

   Presentation: show each product as a "card" set off by a horizontal rule (`---`)
   above AND below. Product title as a markdown heading (`##`) so it's large, with the
   product `id` shown clearly in/next to the title (it's the id used for the save — see
   the HARD ID RULE in Safety) and the `/products/<urlname>` link directly under it.
   Bold field labels (Description:, Bullets:, One-line summary:) and bullets one per
   line. Interactive approval card (show_widget + sendPrompt buttons) button rules:
   * INITIAL suggestion card → ONE button only: "Approve & save".
   * REVISED card (after Lynton's feedback) → two buttons: "Approve & save" + "Revert
     to previous" (revert restores the prior version).
   * No "Next" / "Tweak again" buttons and no AskUserQuestion dialog — Lynton types
     feedback freely.
4. **Draft + suggest** — propose:
   * `product_description` (on-voice, right length, accurate to the real specs)
   * `feature_bullets` (3–5 phrases)
   * `one_line_summary` (if in scope)

   Offer 1–2 options / a quip variant where it helps. Iterate with Lynton.
5. **Approve → write back** (Step 4). Then move to the next product.

## Step 4 — Write back (after approval, per product)

```
update_product
  id: <id>          # REQUIRED — see HARD ID RULE
  product_description: "<approved text>"
  one_line_summary: "<approved text, if in scope>"
  body: "<p>…</p>"  # keep in sync with product_description
```

### feature_bullets — write path UNVERIFIED (don't assume)

`get_products` returns `feature_bullets` as a PHP-serialised string
(`a:4:{i:0;a:1:{i:0;s:16:"Removable covers";}…}`) and the WRITE schema types it as
integer, so writing it is uncertain. It was NOT cleanly tested — during the first run
the `update_product` calls intermittently went out with an EMPTY payload (every call,
incl. a plain `id`+`removal_sku` one that had worked moments before, returned "An `id`
is required"). So that error is NOT proof of a feature_bullets problem — it was a
transmission glitch dropping all params. Before concluding anything: (1) make a
known-good control write (id + one text field) and confirm it returns the record; (2)
only then test `feature_bullets`. If control writes fail, the issue is the call
itself — stop and retry clean, don't blame the data. Confirmed-writable as text:
`product_description`, `one_line_summary`, `body`, `meta_*`. If bullets truly won't
write, hand them to Lynton for the CMS — but verify first.

### Consider keeping `body` in sync

`body` holds the HTML twin of `product_description` (`<p>…</p>`). If the site reads
`body` on some templates, update it too: `body: "<p>…</p>\n"`.

### ⚠️ Full-record validation blocks writes (removal_sku gotcha)

`update_product` validates the ENTIRE product record on save, not just the fields you
pass. If a pre-existing field is invalid by current rules, the whole write fails
atomically (no copy is saved). Confirmed blocker: `product_removal_sku` → "Please
select a valid option", even though a value (e.g. `24609`) is stored — the stored
value is stale / no longer in the valid set (shows as an amber check in admin).
Passing the same stale value back does NOT fix it; a currently-valid option is
required. This likely affects MANY products (removal_sku amber is common). Handle
BEFORE writing copy: detect it, surface to Lynton, get the correct removal_sku (or fix
removal SKUs in a separate pass) — do not guess/auto-change unrelated config. Other
fields may have the same behaviour; expect full-form validation.

## Safety

* ⛔ **HARD ID RULE.** NEVER call `update_product` without an explicit `id` that
  exactly matches the product currently on the card. If the id is missing, blank, or
  in any doubt, STOP — do not save. Saving with the wrong id could overwrite the wrong
  product (catastrophic). Carry the id from the card into the write every time; the id
  MUST be shown on the product card so it's always visible and verifiable.
* **One product per save.** Build the full `update_product` payload (id + the fields)
  in a single call — never emit a save with empty/partial parameters. If a call
  errors, re-check the id before retrying; don't blind-retry.
* These are LIVE active products — confirm each write with Lynton first.
* Report the returned record so the save is verified (echo id + the changed fields).
* **Invalid-field block** (e.g. `removal_sku`): first CHECK the value — search the id;
  if it returns nothing it's a dangling reference. Then TELL Lynton "this has an
  invalid <field> (<value>), I'm going to clear it" BEFORE clearing, then include the
  cleared field in the save.
* `bc_lifecycle_status: "DISCO"` = sell-through (still selling remaining stock), NOT a
  reason to exclude — it can still be web-active and worth copy.
* `update_product` masks GDPR fields in its response — that's expected.

### ⚠️ KNOWN ISSUE (PENDING) — intermittent empty-payload writes

`update_product` calls intermittently arrive at the tool with NO parameters and return
`Error: An id is required to update a product.` — even for a payload that is correct
and identical in shape to one that succeeded moments earlier (id + text fields only).
Observed behaviour:

* It is INTERMITTENT and content-independent: the same
  `id`+`product_description`+`one_line_summary`+`body`+`removal_sku` payload failed
  several times, then went through unchanged on a later attempt. Both the Sloafer Sofa
  (2993) and Footstool (2992) eventually saved this way.
* So "id is required" is NOT diagnostic of a bad id or bad data — it means the params
  didn't transmit. Do NOT conclude the id was lost or a field is unwritable from it.

Working mitigation until root-caused:

* Keep the verified `id` on the product card and re-send the SAME call; it usually
  lands within a couple of attempts. Re-read the record to confirm the save.
* Respect the HARD ID RULE and DON'T spam: a few deliberate retries, not a loop.
* Because `feature_bullets` was only ever attempted DURING this glitch, its
  writability is still genuinely unproven — retest it only once text-only writes are
  transmitting reliably.

ROOT CAUSE: still unknown — needs investigation (possible client-side serialisation /
connector-reconnect timing). This is the top open item before trusting unattended
saves.

## Quick field reference (loaf get_products)

* **Copy:** `product_description`, `product_tagline`, `one_line_summary`,
  `feature_bullets` (PHP-serialized), `body` (HTML), `features`, `meta_title`,
  `meta_description`.
* **Routing/IDs:** `id`, `title`, `urlname`, `type` (product-type id), `status`
  (active / inactive / archived / posoms), `best_seller` ("true"/"false"), `position`.
* **Media:** `listing_image`, `gallery` (comma-separated media IDs; render via the live
  PDP / Cylindo acct 4980 rather than the raw IDs).
