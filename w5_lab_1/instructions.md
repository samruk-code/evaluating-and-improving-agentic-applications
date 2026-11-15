# Module 5, Lab 1: Task guide

Start with [README.md](README.md) to set up your local environment.

These tasks refer to the course interface. Locally, open Phoenix at http://localhost:6006 and the chat app at http://localhost:7860. Give the linked prompt files to your coding assistant, or write your own. The prompts are guides; adapt them freely to meet each task's goal. Saved edits from the lab are already in `prompts/`. The wording you started from is in `prompts/original/`.

### Task 1: Build the test datasets

**Goal:** Have OpenCode save six test questions in Phoenix, as two datasets.

To know whether a fix worked, you need to ask the agent the same questions before
and after it. In this task, you aren't fixing or scoring anything yet, just saving the
list of test questions.

There are two datasets so that you get a separate result for each one.

The **failure set** shows whether a fix worked. These questions test whether the agent
states product details that aren't in the catalog:

| Case | Question | What the catalog has |
|---|---|---|
| `merino wool care` | How should I wash and dry the merino wool sweater? It's TOP-004. | One line: "Machine washable on wool cycle." |
| `hiking shoes materials` | What are the Trail Runner hiking shoes actually made of? SHO-001. | The fabric: synthetic mesh |
| `denim jacket care` | How do I wash the denim jacket without it fading? It's OUT-001. | No care instructions |

The **known-good set** shows whether a fix broke something that already worked, which
is called a **regression**. The agent already gets these questions right:

| Case | Question | What should happen |
|---|---|---|
| `tee size availability` | Do you have the Classic Tee in medium? | The agent checks stock. |
| `in-window refund` | I'm CUST-002. The denim jacket from order 4551 doesn't fit, I'd like a refund. | The agent refunds $98.00. The order is 4 days old. |
| `out-of-window refusal` | CUST-001 here. I want to return order 4530, the tee. | The agent refuses. The order is 45 days old, and the limit is 30. |

1. Send the prompt below to OpenCode. It writes and runs a script that saves both
   datasets. The script also asks the agent the merino sweater question, so you can see
   one example of the failure.
2. Wait for `Datasets created — N failure examples, M known-good examples, printed above.`
   You should see 3 and 3.

[Open this task's prompt](prompts/prompt_task1.md)

**See the datasets**

1. Click **Check Phoenix**, then **Datasets & Experiments** in the sidebar. You should
   see `northwind_faithfulness_failures` and `northwind_known_good`, with 3 examples
   each. An example is one question in a dataset.
2. To see all six questions in one table, click **Data Explorer** and open the Task 1
   tab.

It's safe to run this task again. It reuses the two datasets instead of creating new
ones.

**See one example of the failure**

OpenCode hides most of the output at first, so click the output in the terminal to
expand it. The output has three blocks: what the catalog says, what the agent's tools
returned, and the agent's answer.

Compare the agent's answer with what the tools returned. Anything extra is the failure
this lab tries to fix. That advice may be good, but it didn't come from Northwind. If
the sweater shrinks, the customer can point to Northwind's own agent telling them how
to wash it. This is the `faithfulness_drift` failure from Module 2.



### Task 2: Score the agent as it is now

**Goal:** Have OpenCode ask the agent all six test questions and score its answers.
These scores are your **baseline**, the starting point you'll compare every fix with.

In this task, you aren't fixing anything yet. Phoenix calls this kind of run an
**experiment**: it asks the agent every question in a dataset, scores each answer, and
keeps the results. You'll run one experiment for each dataset.

**Once this task has finished, don't run it again.** The agent doesn't answer the same
way every time, so a second run would change your baseline. If you do run it again,
redo any later tasks you've already done, so that they compare with the new one.

Six evaluators score each answer:

| Evaluator | Type | What it checks |
|---|---|---|
| `tool_selection` | Code, no LLM | Did the agent call the tools the question needs? |
| `tool_invocation` | Code, no LLM | Did it pass the right details, such as the product ID? |
| `outcome` | Code, no LLM | Did a refund happen when it should, and only then? |
| `identity_before_refund` | Code, no LLM | Did it check who the customer is before refunding? |
| `policy_compliance` | LLM judge, written for Northwind | Did it follow Northwind's policy? |
| `response_grounding` | LLM judge, new in this lab | Did every product detail in the answer come from a tool? |

The first five are Module 4's, unchanged. They check what the agent did, so they don't
catch this failure. An answer full of made-up care instructions can still pass all five.

`response_grounding` catches it. This LLM judge compares the agent's answer with what
its tools returned. If every product detail in the answer came from a tool, it labels
the answer `grounded`. If any detail didn't, it labels it `ungrounded`. For example, if
the tool returned only "Machine washable on wool cycle." and the answer also says to
use cold water, that's `ungrounded`. The same goes for care advice when the catalog has
none, even if the agent says "typically" first.

1. Click **Edit grounding_prompt.md** to read the judge's rubric. It's the part between
   the two `` ``` `` lines. Close the editor without changing anything.
2. Send the prompt below to OpenCode. It writes and runs a script that builds the new
   judge and runs both experiments.
3. Allow about 3–5 minutes, even if nothing seems to be happening. Wait for
   `Baseline scored — grounding G% on the failure set, K% on known-good, printed above.`
   If the script stops before this message, send the prompt again.

[Open this task's prompt](prompts/prompt_task2.md)

**Read the results**

Click **View Task 2 dataframe**. Each row is one question, with the tools the agent
called, how long it took, and all six scores.

On the failure set, look at `response_grounding`. You'll usually see this:

| Case | `response_grounding` |
|---|---|
| `merino wool care` | `ungrounded` |
| `hiking shoes materials` | `grounded` |
| `denim jacket care` | `ungrounded` |

The agent doesn't always answer the same way, so your scores may not match these. If a
result surprises you, ask OpenCode to run that question a few more times with the same
prompt and score each answer.

To see what the agent added, click the output in the terminal to expand it. For each
`ungrounded` answer, the judge's explanation names a detail no tool returned.

The agent's prompt may explain why the care questions fail and the hiking shoes question
doesn't. Click **Edit prompts/v1.md** and read the last line:

> Ground product facts in tool results. Do not state a price, fabric, size or
> availability a tool has not given you.

The rule names fabric, which may be why the hiking shoes question passes. It doesn't
name care instructions, which may be why the two care questions fail. Close the editor
without changing anything.

On the known-good set, the scores should mostly be passes. `in-window refund` may come
back `ungrounded` if the agent adds something no tool returned, such as how many business
days the refund takes. That's a different failure from the one you're fixing.

**See the results in Phoenix**

1. Click **Check Phoenix**, open **Datasets & Experiments** in the sidebar, and click
   `northwind_faithfulness_failures`.
2. The **Experiments** tab lists your experiment. Click its name to see each question
   with the agent's answer, its tool calls, and all six scores.
3. To see a full run, go back and click **Traces** in the experiment's row.

**Troubleshooting**

- **The output shows `[1 unscored]`, or says a task run errored:** A judge call or
  connection failed during the run, so the baseline isn't complete. Ask OpenCode to run
  `task2_baseline.py` again.



### Task 3: Test a new rule in the prompt

**Goal:** Have OpenCode add a rule to the agent's prompt, ask the agent all six test
questions again, and compare the new scores with your baseline.

Task 2 suggested a reason for the failure: the rule in the prompt doesn't name care
instructions. This new rule does, and it goes at the end of the prompt:

> GROUNDING:
>
> - Never state a product detail unless a tool result supports it. This
>   includes care and washing instructions, materials, measurements, sizes,
>   colours and prices.
> - If the catalog does not carry a detail the customer asked for, say so
>   plainly rather than filling it in.

You don't know yet whether it will work, which is why you test it. The questions, the
evaluators, and the rest of the prompt all stay the same, so the rule is the only thing
you're changing.

The rule could also cause a new problem. The agent may start looking things up again
when it already has the answer. That adds a tool call and more time, but the answer
still looks fine, and no evaluator flags it. Only the tool call counts and run times
show it.

1. Before you run anything, write down what result would be good enough to ship. You
   can use this one: all three failure-set questions pass, no known-good question gets
   worse, and no known-good question makes more than one extra tool call. If you wait
   until you see results, it's easy to keep changing things because you can always find
   something to improve.
2. Send the prompt below to OpenCode. It writes and runs a script that adds the rule,
   asks all six questions again, and compares the scores with your baseline.
3. Allow about 3–5 minutes. Wait for
   `v2 scored — F fixed on the failure set, R regressed on known-good, C extra tool calls, printed above.`
   In the results, v1 means the original prompt, and v2 means the prompt with this new
   rule.

[Open this task's prompt](prompts/prompt_task3.md)

**Read the results**

Click the output in the terminal to expand it. It compares the old and new scores one
question at a time. For example, the failure set might look like this:

| case | before | after | change |
|---|---|---|---|
| denim jacket care | 0.0 | 1.0 | FIXED |
| hiking shoes materials | 1.0 | 1.0 | pass |
| merino wool care | 0.0 | 1.0 | FIXED |

- `before` is the `response_grounding` score with the original prompt, and `after` is
  the score with the new rule. 1.0 is a pass, and 0.0 is a fail.
- `FIXED` means a fail became a pass, and `REGRESSED` means a pass became a fail.
- `pass` and `fail` mean the result stayed the same.
- `?` means a run wasn't scored, so ask OpenCode to run `task3_v2.py` again.

Here's what to look for:

- **On the failure set,** you want `FIXED`.
- **On the known-good set,** you don't want `REGRESSED`, because it means the rule may
  have broken something. You may see `FIXED` on `in-window refund`, because the rule
  often stops the extra refund details from Task 2.

Go by these rows, not the overall pass rate. If one question gets fixed and another
breaks, the pass rate doesn't move. One `FIXED` or `REGRESSED` may not repeat, so if a
result surprises you, have OpenCode run that question a few more times, as in Task 2.

To see the tool calls on the known-good set, click **View Task 3 dataframe**. For example:

| case | calls_v1 | calls_v2 | extra_calls |
|---|---|---|---|
| in-window refund | 4 | 4 | 0 |
| out-of-window refusal | 3 | 3 | 0 |
| tee size availability | 2 | 3 | 1 |

In this example, the new rule added one tool call to the tee question. The agent doesn't
always call the same tools, so your numbers may not match these. If you see no extra
calls, that's fine. The terminal output also shows how long each run took, and it's the
only place that shows `outcome` and `policy_compliance`.

Then ask whether the change was worth what it cost. If wrong product details could
seriously mislead a customer, an extra tool call may be a fair price. If tool calls are
slow or expensive for your application, it may not be.

To see the full prompt, click **Edit prompts/v2.md**, then close the editor without
changing anything.

**Compare two runs in Phoenix**

If a question regressed or got an extra tool call, compare its two runs:

1. Click **Check Phoenix**, open **Datasets & Experiments**, and click the question's
   dataset.
2. Tick the boxes next to the two experiments, then click **Compare**. On the known-good
   set, they're `baseline-v1-known-good` and `grounding-rule-v2-known-good`. On the
   failure set, the names end in `-failures`. If a name appears twice, tick the newest
   one.
3. Find the question, and look for the first tool call that's different.



### Task 4: Test two more fixes and decide what to ship

**Goal:** Have OpenCode test two more fixes: care instructions added to the catalog for
one product, and a narrower rule in the prompt. Then decide which prompt you'd ship.

**The data fix.** The videos' **intervention hierarchy** lists where to look for a fix,
simplest first: data, prompt, tools and workflow, model, settings. You went straight to
the prompt in Task 3, but the hierarchy checks data first. The catalog has no care
instructions for the denim jacket. This fix adds these, and uses the original prompt so
that the catalog is the only change:

> Machine wash cold inside out, tumble dry low. Wash separately for the first three
> washes.

**The narrower rule.** The rule in Task 3 may have added tool calls. This one replaces
it. It only covers care, materials, and measurements, and allows one lookup per question.

1. Send the prompt below to OpenCode. It writes and runs two scripts:
   - The first adds the denim jacket's care instructions, asks the three failure-set
     questions again, and then takes the instructions back out. That way, the narrower
     rule gets tested on the same catalog as the others.
   - The second adds the narrower rule and asks all six questions again. In the results,
     v3 means the prompt with this rule.
2. Allow about 5–8 minutes. Wait for
   `Data fix scored — G% grounding with the same prompt, catalog reverted, printed above.`
   and then `v3 scored — grounding G% on the failure set, T tool calls on known-good, printed above.`

[Open this task's prompt](prompts/prompt_task4.md)

**Read the data fix results**

1. Check that the catalog went back to how it was. Click the output in the terminal to
   expand it. It counts the products with care instructions three times, like
   `{'written': 1, 'total': 20}`. `written` should go 1, 2, 1. If it doesn't end at 1,
   the script stopped early. Before you do anything else, ask OpenCode to run
   `db.set_care(db.get_connection(), {'OUT-001': ''})`. Then send the prompt again.
2. Click **View Task 4 data-fix dataframe**. It compares the grounding scores with and
   without the data fix.

The data fix can help the denim question, but not the merino question. The merino
sweater already has care instructions, and the failure is the agent adding to them. If
merino shows `FIXED` here, that's the agent's answers varying, not the data fix.

The fix doesn't always help the denim question either. If denim still fails, ask
OpenCode to print the judge's explanation for it. Usually, the agent quoted the new care
instructions and then added advice of its own, such as avoiding hot water.

So the two kinds of fix do different jobs. A prompt rule tells the agent not to make up
details, but then it can only say the catalog doesn't list them, and the customer still
doesn't know how to wash the jacket. A data fix gives it something true to say. In
practice, you'd do both: ship the rule now, and file a ticket to fill in the catalog.

**Compare the three prompts**

1. Click **View Task 4 three-way dataframe**. It shows the grounding scores and tool calls
   for v1 (the original prompt), v2 (the rule from Task 3), and v3 (the narrower rule).
   Look for the prompt that passes the failure set without adding tool calls. If
   `in-window refund` passes only under v2, that's because v2's rule can stop the extra
   refund details from Task 2, and v3's rule doesn't cover them.
2. The three-way table leaves out `outcome` and `policy_compliance`, so it can't show a
   broken refund or refusal. Check them in the terminal output's summary of v3 on the
   known-good set, and compare them with your baseline in the Task 2 tab of **Data
   Explorer**. If one dropped, use step 3 to find the question.
3. To read the answers side by side, use **Compare** in Phoenix, as in Task 3. Tick
   `baseline-v1-failures`, `grounding-rule-v2-failures`, and `scoped-rule-v3-failures`. On
   the known-good set, the names end in `-known-good`. If a name appears twice, tick the
   newest one.

To read the narrower rule, click **Edit prompts/v3.md**, then close the editor without
changing anything.

**Decide what to ship**

Choose v1, v2, or v3, and check your choice against the result you wrote down in Task 3.
If none meets it, note which came closest and what you'd try next.

On a real project, stop editing the prompt once it meets that result, even if you could
still improve it. Each extra edit is another chance to break something that works, such
as the refusal on order 4530.

**Finish with a few notes.** Answer these for yourself:

1. Which of v1, v2, and v3 would you ship, and which results are your evidence?
2. What would make you stop even if another prompt edit might raise the score?
3. You tested a judge against reviewed labels in Module 3. What would make you do that
   again after this agent changed?

Every question in this lab was written for the test, and real customers will ask things
differently. As you saw in the Module 5 videos, each real failure worth fixing becomes a
new test case, and fixed failures stay in your test sets so that later changes can't bring
them back.



### Working in the terminal (optional)

You don't need this section to complete the lab. It shows the terminal
commands and code behind each task, for when you want to see what OpenCode
does or fix a problem yourself. OpenCode writes its own scripts, so the
code it produces will differ in the details.

**Switching between OpenCode and the terminal**

- To close OpenCode and work directly in the terminal, type `/exit` in
  OpenCode, or press `Ctrl+C` twice. You'll see a plain command prompt.
- To reopen OpenCode, type `opencode` and press `Enter`.

**Before you begin: Phoenix and the agent**

On the platform, both start automatically. If you need to check or restart
them:

- Read the last lines of Phoenix's log: `tail -n 50 phoenix.log`
- Check whether Phoenix is running: `pgrep -af 'phoenix serve'`
- Restart Phoenix with its data:
  `PHOENIX_DATA_DIR=./phoenix-data bash phoenix-start.sh`
- Read the agent's log: `tail -n 50 app.log`
- Restart the agent: `bash run.sh`
- Restart the chat app with another prompt:
  `NORTHWIND_PROMPT_VERSION=v3 bash run.sh`

Don't delete the `phoenix-data` folder or `northwind.db`. They hold your
datasets, experiments, and traces, and the store database.

**See the store database**

`db.py` opens the store database. To see how many products have care
instructions, and to list every refund:

```bash
python3 -c "import db; print(db.care_coverage(db.get_connection()))"
python3 -c "import db; print([dict(r) for r in db.get_connection().execute('SELECT * FROM refunds')])"
```

**Task 1: Build the test datasets**

`create_or_get` in `exp_utils.py` makes each dataset, or reuses it if it already
exists:

```python
client.datasets.create_dataset(
    name=name,
    inputs=[{"question": row["question"]} for row in rows],
    outputs=[{} for _ in rows],
    metadata=[to_metadata(row, split) for row in rows],
)
```

What a correct run looks like travels with each example, in its `metadata`. In
Module 4, it was in a lookup keyed on the question's text.

**Task 2: Score the agent as it is now**

`run_experiment_on` in `exp_utils.py` runs one experiment:

```python
async def run_northwind_agent(input):
    return await ask_agent(input["question"], prompt_version)

await async_run_experiment(
    dataset=dataset,
    task=run_northwind_agent,
    evaluators=evaluators,
    experiment_name=label,
)
```

Phoenix calls the function that runs the agent on one example a **task**. That's
Phoenix's word for it, not one of this lab's tasks. `ask_agent` returns the answer,
the tool calls, the time taken, and the prompt version, so nothing has to be rebuilt
from Phoenix as in Module 4. Evaluators receive what they need by argument name,
such as `input`, `output`, and `metadata`:

```python
@create_evaluator(kind="LLM", name="response_grounding")
async def response_grounding(input, output):
    score = await judge(grounding_classifier, {
        "input": input["question"],
        "trajectory_text": format_trajectory(output["trajectory"]),
        "output": output["response"],
    })
    return score.score, score.label, score.explanation
```

**Task 3: Test a new rule in the prompt**

```python
compare(base_f, v2_f, "response_grounding", "FAILURE SET, v1 -> v2")
costs = cost_table(base_kg, v2_kg, "v1", "v2")
```

`python3 task3_v2.py` runs the whole task again, including rebuilding
`prompts/v2.md` from v1.

**Task 4: Test two more fixes and decide what to ship**

```python
before = db.care_snapshot(conn, list(CARE_BACKFILL))
db.set_care(conn, CARE_BACKFILL)  # fill in the jacket's care field
# run the failure set on v1, and compare it with the baseline
db.set_care(conn, before)  # put the catalog back
```

```python
three_way([("v1", base_f), ("v2", v2_f), ("v3", v3_f)], "response_grounding", "FAILURE SET")
```

**Progress circles**

Each task's progress circle turns green when that task's Data Explorer tab
exists: `task1-datasets`, `task2-baseline`, `task3-v2`, and `task4-three-way`.
So Task 4's circle waits for the narrower rule, the second of its two scripts.



---
