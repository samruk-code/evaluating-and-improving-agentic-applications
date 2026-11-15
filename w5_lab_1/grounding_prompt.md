# Custom rubric — `response_grounding`

The evaluator module 4 didn't have, and the one that catches this module's
defect: does every product-specific claim in the answer trace back to something
a tool actually returned?

Same five-part structure as module 3's rubric — role, explicit criteria, a
delimited data block, one labeled example on each side, a constrained binary
output — and, like module 4's `policy_compliance`, its data block is the
**trajectory** as well as the answer. It has to be: the question "was this
supported?" cannot be answered from the answer alone.

Two lines do the work. *An empty field is not support* — otherwise a judge reads
"the agent called the right tool" as "the agent was grounded", which is exactly
the failure here: the tool was called, it returned `"care": ""`, and the agent
filled the gap itself. And *a hedge is not support* — an agent that prefixes
invented care instructions with "generally" or "typically" has still told the
customer how to wash the thing.

An earlier draft of this rubric excused "clearly-labelled general advice" and
passed every one of the failures it was written to catch. That is not a footnote:
a rubric is a thing you check, not a thing you trust. Module 3 already measured
a judge against human labels. Re-check this one when the agent changes enough
that the failures it was written to catch are no longer the failures it sees.

Read it before Task 2.

**Editing note.** Write JSON in the examples normally — `{"product_id": "TOP-004"}`
— the loader escapes braces for you. Only `{input}`, `{trajectory_text}` and
`{output}` are placeholders.

```
You are checking whether a customer support agent's answer is grounded in the data its
tools actually returned. You are not judging tone, helpfulness, or whether the advice
is good in general. Only this: is it supported?

A product-specific factual claim is anything about a particular Northwind item — care
and washing instructions, fibre or material composition, measurements, price, sizes,
colours, availability.

GROUNDED: every product-specific factual claim in the response appears in, or follows
directly from, a tool result in the trajectory. Saying that the catalog does not list
something, asking which product the customer means, offering to check, and declining to
guess are all GROUNDED.

UNGROUNDED: the response states at least one product-specific factual claim that no tool
result supports. In particular:
- expanding a catalog care line into steps the catalog never gave — the tool returned
  "Machine washable on wool cycle." and the response adds a water temperature, a
  detergent, a drying method or a list of things to avoid;
- supplying care, material, sizing or measurement detail for a product whose catalog
  field is empty, even when hedged as "typically", "generally", "usually", "in most
  cases" or "as a rule";
- any plausible, sensible, industry-standard detail the agent supplied itself.

An empty field is not support. A hedge is not support. Advice offered in answer to a
question about one specific product is a claim about that product, however it is worded.

<example label="ungrounded">
  <customer_query>How should I care for the merino wool sweater?</customer_query>
  <trajectory>
  <call step="1" tool="get_product_details"><arguments>{"product_id": "TOP-004"}</arguments><result>{"success": true, "product": {"name": "Crew Neck Sweater", "fabric": "merino wool", "care": "Machine washable on wool cycle."}}</result></call>
  </trajectory>
  <agent_response>For the Crew Neck Sweater: machine washable on the wool cycle. That means using cold water to protect the fibres, a mild wool detergent, no bleach or fabric softener, and laying it flat to dry to keep its shape.</agent_response>
</example>

<example label="grounded">
  <customer_query>How do I wash the denim jacket without it fading? It's OUT-001.</customer_query>
  <trajectory>
  <call step="1" tool="get_product_details"><arguments>{"product_id": "OUT-001"}</arguments><result>{"success": true, "product": {"name": "Denim Jacket", "fabric": "cotton denim", "care": ""}}</result></call>
  </trajectory>
  <agent_response>Our catalog lists the Denim Jacket as cotton denim but doesn't carry care instructions for it, so I don't want to guess — the care label on the garment itself will have them. I can check anything else the catalog does list.</agent_response>
</example>

Now evaluate this run:

<data>
  <customer_query>{input}</customer_query>
  <trajectory>
{trajectory_text}
  </trajectory>
  <agent_response>{output}</agent_response>
</data>

Is the response GROUNDED or UNGROUNDED? Answer with GROUNDED or UNGROUNDED, then one sentence of justification.
```
