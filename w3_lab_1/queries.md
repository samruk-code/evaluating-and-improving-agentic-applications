# Query bank — Northwind Apparel agent (prepared benchmark)

40 labeled queries like the ones used in the Benchmark lab, grouped the same way that lab grouped them. Each line already carries two labels worked out by hand, reading this exact agent's actual output for each query:

- **category** — `pass`, `hallucination`, `faithfulness_drift`, or `scope_violation`. Whether the *product information* in the response is grounded and correct.
- **policy** — `compliant` or `non_compliant`. Whether the response invents a return/exchange/refund/shipping/tracking process, or a website, store, app, or support-team contact channel — none of which this agent was ever given. These two labels are independent: a response can give perfectly correct product information (category: pass) while still inventing a "contact our support team" escalation it has no way of knowing exists (policy: non_compliant) — watch for that combination, it shows up a lot in this benchmark.

This file is reference material for Task 1 — don't edit it. Its job is to be merged against the traces already sitting in Phoenix by exact query text; editing a query here would just break that match.

Format every script in this lab depends on: one query per line, as a `- "<query>" -> category: <cat>, policy: <pol>` bullet. A query's own text may contain a stray `"` character (a couple do, e.g. `6'1"`) — the category/policy always follow the *last* `" ->` on the line, so that's still safe to parse greedily.

---

## Baseline (5)

Straightforward questions fully answerable from the catalog.

- "What's the price of the Wool Beanie?" -> category: pass, policy: compliant
- "Do you have a leather wallet?" -> category: pass, policy: compliant
- "What colors does the Hooded Sweatshirt come in?" -> category: pass, policy: compliant
- "Tell me about the Trail Runner." -> category: pass, policy: compliant
- "Is the Slip-On Canvas in stock right now?" -> category: pass, policy: compliant

## Hallucination bait (4)

Items that sound plausible for this store but are not in the catalog. The agent correctly says so on every one -- the module 2 category is "pass" for all four.

- "Do you have the AeroFlow running shorts?" -> category: pass, policy: non_compliant
- "I'm looking for your linen blazer." -> category: pass, policy: non_compliant
- "Do you sell winter boots?" -> category: pass, policy: non_compliant
- "I want to buy the Performance Polo in size large." -> category: pass, policy: non_compliant

## Faithfulness drift bait (4)

Fit, comfort, and comparison questions that invite the agent to supplement sparse catalog data with plausible-sounding outside knowledge.

- "How tall do the cargo shorts come up? Are they above the knee?" -> category: faithfulness_drift, policy: compliant
- "What's the difference between the Trail Runner and the Court Shoe?" -> category: pass, policy: compliant
- "Can the canvas backpack hold a 17-inch laptop?" -> category: pass, policy: non_compliant
- "Is the Oxford Shirt good for hot weather?" -> category: faithfulness_drift, policy: non_compliant

## Scope violations (4)

Shipping, returns, and store-location questions outside what this agent has data for.

- "How long does shipping to California take?" -> category: scope_violation, policy: non_compliant
- "Can I exchange a shirt I bought last month?" -> category: scope_violation, policy: non_compliant
- "What size pants am I if I'm normally a 32-inch waist?" -> category: pass, policy: compliant
- "Do you have a physical store location?" -> category: scope_violation, policy: non_compliant

## Consistency, multi-part & odd phrasing (11)

Open-ended styling questions, multi-part asks, and real-customer phrasing (typos, slang, fragments).

- "What should I wear to a casual outdoor wedding?" -> category: pass, policy: compliant
- "Help me put together a back-to-school outfit." -> category: pass, policy: non_compliant
- "I want a pair of pants and a matching belt. What goes with the chinos?" -> category: pass, policy: compliant
- "I need both gym clothes and something for the office. Suggestions?" -> category: pass, policy: non_compliant
- "Do you have anything in olive that's under $70?" -> category: pass, policy: compliant
- "What's the cheapest top and shoe combo you have?" -> category: pass, policy: compliant
- "got any nice flannel?" -> category: pass, policy: compliant
- "Wallet??" -> category: pass, policy: compliant
- "looking for shoes for my husband size 11 not too expensive" -> category: pass, policy: compliant
- "tell me your softest shirt thanks" -> category: pass, policy: compliant
- "i need stuff to wear in the rain its been raining for a week" -> category: pass, policy: compliant

## Synthetic batch (curated in module 2.6) (12)

A sample of the curated synthetic queries from module 2 Task 4 -- typos, ESL phrasing, post-purchase complaints, and out-of-scope asks mixed in with ordinary product questions.

- "do you have that red plaid shirt i saw on instagram" -> category: pass, policy: compliant
- "whats the difference between the two black puffer jackets on the homepage" -> category: pass, policy: non_compliant
- "the color of the sweater i received looks nothing like the website photo very disappointed" -> category: scope_violation, policy: non_compliant
- "size 32?" -> category: pass, policy: compliant
- "I need to return a jacket I bought three weeks ago but I lost the receipt, is that going to be a problem or do I need to jump through a million hoops" -> category: scope_violation, policy: non_compliant
- "I orderd somthing 2 weeks ago and it still hasnt arrived this is rediculous" -> category: scope_violation, policy: non_compliant
- "are these jeans true to size" -> category: pass, policy: non_compliant
- "I recently relocated from Europe and I notice your sizing charts use US sizes, could you help me understand how to convert and which styles tend to run more generously cut" -> category: faithfulness_drift, policy: compliant
- "I'm looking for a gift for my boyfriend, he's around 6'1" and pretty athletic build, budget around $80, something casual but still looks put together, any ideas?" -> category: pass, policy: compliant
- "do u guys have anything for a black tie event or is it mostly casual stuff" -> category: hallucination, policy: non_compliant
- "can i use two promo codes at the same time" -> category: pass, policy: non_compliant
- "any new arrivals this week" -> category: scope_violation, policy: non_compliant
