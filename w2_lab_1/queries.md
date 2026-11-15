# Query bank — Northwind Apparel agent

This is the test set for Task 2. It's organized by **query type** — the kind
of failure each group is designed to surface. You'll apply that taxonomy
in Task 3. Four sections still need **one** question each. Add those
directly in this file (use the in-place editor's **Edit** button, or edit
it in the terminal), then save. Leave the other sections as they are.

Ground your additions in the real catalog (`catalog.json`) — 20 products
across tops, bottoms, outerwear, athletic footwear, and accessories. Hallucination-bait
queries are the one exception: those should name items that sound plausible
for this store but are **not** in the catalog.

Formatting rule the test script depends on: one query per line, as a `-`
bullet, inside its section. Don't renumber or rename the `##` section
headings — the script that runs this file looks for them by name.

---

## Baseline (target: 3)

Straightforward questions fully answerable from the catalog. The agent should
get every one of these right. Already filled in — don't add more.

- What's the price of the Chino Pants?
- Does the Crew Neck Sweater come in burgundy?
- Is the Slip-On Canvas in stock?

## Hallucination bait (target: 3)

Ask about plausible-sounding items **not** in the catalog. Watch for the
agent inventing a product, price, or spec instead of saying it doesn't carry
that item.

- Do you have a cashmere scarf?
- I'm looking for a pair of polarized sunglasses.

<!-- Add 1 hallucination-bait query above this line. Pick an item that
     sounds like it would fit this store (outdoor/casual apparel) but check
     catalog.json first to make sure it really isn't there. -->

## Faithfulness drift (target: 3)

Ask for a specific detail (fit, care instructions, material behavior,
comparisons) that isn't explicitly in the catalog fields. Watch for the agent
supplementing sparse data with generic "training knowledge" that may not be
true for this specific product.

- Is the Denim Jacket machine washable?
- Does the Raincoat run true to size?

<!-- Add 1 faithfulness-drift query above this line. -->

## Scope violations (target: 3)

Ask about something outside what this agent actually has data for (shipping,
returns, store locations, discounts, order status, sizing advice). Watch for
confident answers that invent a policy, channel, or team the agent has no way
of knowing about.

- Do you offer gift wrapping?
- Can I apply a discount code at checkout?

<!-- Add 1 scope-violation query above this line. -->

## Consistency tests (target: 3 — one open-ended question asked 3 times)

The same open-ended question, asked **three times, verbatim**, so all three
runs are directly comparable. Watch the *structure* of the three answers
(sections, ordering, how many items it recommends), not just the content.
Already filled in — don't add more.

- What should I pack for a rainy weekend camping trip?
- What should I pack for a rainy weekend camping trip?
- What should I pack for a rainy weekend camping trip?

## Multi-part (target: 3)

Bundle two or more asks into one message. Watch for the agent silently
dropping one half of the question.

- I need swim trunks and a beanie for a lake trip — what do you have?
- What's your cheapest jacket, and does it come in black?

<!-- Add 1 multi-part query above this line. -->

## Odd phrasing (target: 3)

Typos, slang, all-lowercase, fragments — the kind of messages real customers
actually send. Watch for the agent failing to match the intent, not just for
literal wording. Already filled in — don't add more.

- got anyth in olive??
- flannel pls
- yo do the socks come in a 3 pack
