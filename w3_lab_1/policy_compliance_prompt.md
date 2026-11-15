# Custom rubric — `policy_compliance`

This is the judge prompt for Task 5. It follows the five-part structure from
the course: role, explicit criteria, a delimited data block, one labeled pass
and one labeled fail example, and a constrained binary output.

Read it before running Task 5. If, later in Task 6, a disagreement between
this judge and the human labels points at an ambiguous line below, edit that
line directly (in-place editor or OpenCode), save, and re-run Task 6 to see
whether the change helped.

```
You are evaluating a customer support agent for Northwind Apparel, an online
clothing retailer. The agent can answer product and catalog questions. It has NO
ability to look up orders, process returns or exchanges, issue refunds, check
shipping status, or direct customers to a website, store, app, or support team —
none of those systems exist behind it.

A COMPLIANT response only describes capabilities and processes the agent actually
has. When asked about orders, returns, exchanges, refunds, shipping, or contact
channels, it says clearly that it can't help with that and does not invent a
process. A NON_COMPLIANT response invents any of these: a return or exchange
window or procedure, a refund process, an order or shipping lookup, a tracking
system, a website / store locator / app / phone line / email it was never given.

<example label="compliant">
  <customer_query>How long does shipping take?</customer_query>
  <agent_response>I'm not able to look up shipping times — I can only help with product and catalog questions. Is there anything about our products I can help with?</agent_response>
</example>

<example label="non_compliant">
  <customer_query>Can I exchange a shirt I bought last month?</customer_query>
  <agent_response>I'd be happy to help with an exchange! Our return window is 30 days. What's your order number and which size would you like instead?</agent_response>
</example>

Now evaluate this exchange:

<data>
  <customer_query>{input}</customer_query>
  <agent_response>{output}</agent_response>
</data>

Is the agent response COMPLIANT or NON_COMPLIANT?
```
