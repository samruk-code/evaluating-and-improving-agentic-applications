# Module 3, Lab 1: Task guide

Start with [README.md](README.md) to set up your local environment.

These tasks refer to the course interface. Locally, open Phoenix at http://localhost:6006 and the chat app at http://localhost:7860. Give the linked prompt files to your coding assistant, or write your own. The prompts are guides; adapt them freely to meet each task's goal. Saved edits from the lab are already in `prompts/`. The wording you started from is in `prompts/original/`.

### Task 1: Build the labeled dataframe

**Goal:** Build the table you'll use for the rest of the lab. Each row has a
question, the agent's answer from Phoenix, and the reviewer's labels from
`queries.md`.

For example, two answers look like this:

| Column | First example | Second example |
|---|---|---|
| `input` (the question) | What's the price of the Wool Beanie? | are these jeans true to size |
| `output` (the agent's answer) | The Wool Beanie is priced at $22.00... | I wasn't able to find any jeans... Contact our support team... |
| `context.span_id` | `5842bc07...` | `96cc961a...` |
| `category` | `pass` | `pass` |
| `policy` | `compliant` | `non_compliant` |

`context.span_id` is the ID that links each row back to its trace in Phoenix.

`category` says whether the product information is right. It's either `pass`
or a failure type from Module 2, such as `hallucination`.

The agent only knows about products and stock, so `policy` checks whether it
pretends to know about anything else, like returns or customer support.
Telling a customer to call a support team is `non_compliant`, because the
agent has no idea whether that team exists.

1. Send the prompt below to OpenCode. It writes and runs a script that finds
   each question from `queries.md` in Phoenix's traces and builds the table.
2. Wait for `Labeled dataframe built — 40 rows, category and policy counts printed above.`
   Phoenix has 57 traces or more, but only 40 of those questions have labels
   in `queries.md`, so the table has 40 rows.

[Open this task's prompt](prompts/prompt_task1.md)

Check that the output shows:

- `category`: 29 `pass`, 7 `scope_violation`, 3 `faithfulness_drift`, and
  1 `hallucination`
- `policy`: 21 `compliant` and 19 `non_compliant`

To see the full table, click **Data Explorer**.

**Troubleshooting**

- **The table has 0 rows:** Phoenix may still be starting. Wait a minute, then
  send the prompt again.
- **The table doesn't have 40 rows:** Ask OpenCode why. If you asked the chat
  app a question from `queries.md`, that adds an extra row, so ask OpenCode to
  keep only the earliest answer to each question.



### Task 2: Prepare and split the dataset

**Goal:** Split the table from Task 1 into two sets: 25 rows to build your
evaluators with, and 15 rows to test on later.

You need two sets because an evaluator will tend to do well on the answers you
used to build it. That doesn't tell you how it will do on new answers. So you
keep 15 answers back for a test in Task 6.

1. Send the prompt below to OpenCode.
2. Wait for `Dataset split — 25 train / 15 test (stratified on policy).`
   `train` is your 25 rows, and `test` is your 15. "Stratified on policy" means
   both sets get about the same mix of `compliant` and `non_compliant` answers.

[Open this task's prompt](prompts/prompt_task2.md)

The output should show 8 `compliant` and 7 `non_compliant` rows in the test
set. To see which rows went where, click **Data Explorer**, open the Task 2
tab, and look at the `split` column.



### Task 3: Build a code evaluator

**Goal:** Have OpenCode build your first evaluator, `product_exists`, and run
it on your 25 rows. It checks whether an answer mentions a product Northwind doesn't sell.

This evaluator is plain code, with no LLM. It looks for five words: `jeans`,
`blazer`, `polo`, `tuxedo`, and `loafers`. If an answer contains any of them,
it gets a `fail`. Otherwise, it gets a `pass`.

1. Send the prompt below to OpenCode.
2. Wait for `product_exists logged — N failures of 25 rows.`
3. Click **Data Explorer**, open the Task 3 tab, and read the answers labeled
   `fail`. You may notice that many of them aren't real problems. Look at the
   following examples:

   | Answer | Why it failed |
   |---|---|
   | I wasn't able to find any jeans... | It contains "jeans". |
   | I sincerely apologize for the inconvenience! | "apologize" contains "polo". |

   Neither answer offers a product Northwind doesn't sell. In the first, the
   agent says it doesn't have jeans. The second has nothing to do with polo
   shirts.

   The check doesn't understand what an answer says. It only searches for those
   exact letters, in that order, anywhere in the text, even in the middle of
   another word. It also can't catch a made-up product that isn't one of the
   five words. Code is that literal. In Task 4, you'll use an LLM judge, which
   reads the answer and can judge what it means.

[Open this task's prompt](prompts/prompt_task3.md)

**See the result in Phoenix**

Each result is also saved on its trace in Phoenix, as a note called an
**annotation**.

1. Copy a few words from a question in the Task 3 table.
2. Click **Check Phoenix** and open the `dlai-ecommerce-agent` project.
3. Replace the text in the filter box above the list with the line below. Put
   your words between the quotation marks, and press `Enter`.

   ```
   "your words" in input.value
   ```

4. Click the `ask_agent` row. Near the top of its **Info** tab, the
   **Annotations** section lists `product_exists`. Click it to see the result.

**Troubleshooting**

- **The list in Phoenix is empty:** Set the time range to **Last 30 days** or
  **Last month**.
- **The annotation isn't there:** Wait 20 seconds, then click **Refresh** at the
  top right of the Phoenix panel. **Refresh** goes back to Phoenix's home page,
  so open the project and the trace again.



### Task 4: Run a built-in LLM judge

**Goal:** Have OpenCode run `CorrectnessEvaluator` on your 25 rows. This
evaluator is built into Phoenix. It's an LLM judge: a model that reads each
question and answer, and decides whether the answer is correct.

A judge needs three things:

- **A model to do the judging.** This lab uses Claude Sonnet, a more capable
  model than the Claude Haiku model that runs the agent.
- **A rubric,** the written criteria the judge follows. `CorrectnessEvaluator`
  comes with its own, so you don't have to write one. It checks whether an
  answer is accurate, complete, and logically consistent.
- **The answers to judge.** The judge only sees each question and the agent's
  answer. It doesn't see the catalog.

1. Send the prompt below to OpenCode. It writes and runs a script that has the
   judge label your 25 rows, and saves the results on their traces in Phoenix.
2. Allow about 1 minute. Wait for
   `correctness logged — label breakdown printed above.`
3. Click **View Task 4 dataframe**. The `label` column is the judge's decision,
   and `category` is the reviewer's. A judge's `correct` should line up with a
   reviewer's `pass`. Look for rows where they disagree.

[Open this task's prompt](prompts/prompt_task4.md)

**See the judge's reason in Phoenix**

Open the same trace you opened in Task 3. It now has a second annotation,
`correctness`. Click it to read why the judge chose that label. The code check
in Task 3 can't give you a reason, but an LLM judge can.

This judge only knows about correctness, not Northwind's rules. It can label an
answer `correct` even if the agent made up a returns process. Task 5 checks for
that.



### Task 5: Run a custom LLM judge

**Goal:** Have OpenCode run `policy_compliance` on your 25 rows. This is an LLM
judge written for Northwind. It checks the same thing as the reviewer's `policy`
label from Task 1: did the agent pretend to know about anything beyond products
and stock?

`CorrectnessEvaluator` can't check this, because it doesn't know what the agent
is and isn't able to do. So this judge has its own rubric, which you'll read in
step 1. The rubric has the five parts from the videos:

1. **Role:** what the judge is evaluating, and what the agent can and can't do.
2. **Criteria:** what makes an answer compliant or non-compliant.
3. **Inputs:** the question and the answer. `{input}` and `{output}` mark where
   they go.
4. **Labeled examples:** one compliant answer and one non-compliant answer.
5. **Output instructions:** the judge has to answer with one of two labels. The
   rubric writes them in capitals, but your results show `compliant` and
   `non_compliant`.

Now run the judge:

1. Click **Edit policy_compliance_prompt.md**. The rubric is the part between
   the two `` ``` `` lines. Read it, then close the editor without changing
   anything.
2. Send the prompt below to OpenCode. It writes and runs a script that has the
   judge apply this rubric to your 25 rows, and saves the results on their
   traces in Phoenix.
3. Allow about 1 minute. Wait for
   `policy_compliance logged — label breakdown printed above.`
4. Click **View Task 5 dataframe**. The `label` column is the judge's decision,
   and `policy` is the reviewer's. Look for rows where they disagree. In Task 6,
   you'll measure how well they agree.

[Open this task's prompt](prompts/prompt_task5.md)

**See the results in Phoenix**

Open the same trace you opened in Task 3. It now has all three annotations:
`product_exists`, `correctness`, and `policy_compliance`.

You can also use the filter box to find answers that one judge passed and the
other didn't. Replace the text in the filter box with this line, and press
`Enter`:

```
annotations['correctness'].label == 'correct' and annotations['policy_compliance'].label == 'non_compliant'
```

These answers got their facts right, but the agent still pretended to know
something it doesn't, such as how to reach a support team. That's why you need
this judge: checking for correct answers alone would miss them.

**Troubleshooting**

- **An annotation is missing:** Check that you opened one of your 25 rows. The
  questions in the Task 5 table are all from those rows. If only `correctness`
  is missing, send the Task 4 prompt again.



### Task 6: Validate the custom judge

**Goal:** Have OpenCode run `policy_compliance` on the 15 rows you kept back,
then compare its labels with the reviewer's. This tells you whether you can
trust the judge. The prompt calls this a **meta-evaluation**: an evaluation of
the evaluator.

As a reminder, a human reviewer has already labeled these 15 answers, so you
have something to compare the judge against. The judge can't see those labels.

1. Send the prompt below to OpenCode.
2. Allow about 30–45 seconds. Wait for
   `Meta-evaluation complete — kappa=X.XXX, D disagreements of 15 test rows.`
3. Find the scores in the output. Read precision and recall in the
   `non_compliant` row of the report.

[Open this task's prompt](prompts/prompt_task6.md)

**What the scores mean**

The output has three scores. For example, suppose the reviewer labeled 7 of the
15 answers `non_compliant`. The judge labeled 6 answers `non_compliant`, and
the reviewer agrees on 5 of those.

- **Precision** would be 5 out of 6, or 0.83. It tells you how often the judge
  is right when it flags an answer. Low precision means false alarms.
- **Recall** would be 5 out of 7, or 0.71. It tells you how many of the real
  problems the judge caught. Low recall means problems get through to customers.
- **Cohen's kappa** tells you how much the judge and the reviewer agree, beyond
  what you'd expect by chance. 1 means they agree on every label, and 0 means
  they do no better than chance. A high score doesn't prove they're right,
  because they can agree and both be wrong.

With only 15 rows, a single answer moves these scores a lot. So read the
disagreements too.

**Read the disagreements**

The output lists each disagreement with the judge's reason. To see all 15 rows,
click **View Task 6 dataframe**: `human` is the reviewer's label, and `judge` is
the judge's. To read the agent's answer, click **Data Explorer**, open the Task 2
tab, and find the question.

For each disagreement, decide which of these happened:

- The judge applied the rubric wrongly.
- The rubric isn't clear enough.
- The reviewer's label is wrong. If so, the label needs fixing, not the rubric.

**Improve the rubric**

1. Write down your three scores, because running the task again replaces them.
2. Ask OpenCode to save a copy of `policy_compliance_prompt.md` as
   `policy_compliance_prompt_v1.md`, so you can go back to it.
3. Pick a disagreement where the judge was wrong or the rubric isn't clear. Click
   **Edit policy_compliance_prompt.md** and make **one** change to the rubric.
   Keep `{input}`, `{output}`, and the two `` ``` `` lines. Click **Save**.
4. In OpenCode, type `Run meta_eval.py again` and press `Enter`.
5. Compare the new scores with your first ones. A change can raise recall by
   adding false alarms, so keep it only if the judge improved overall.

If there are no disagreements, try removing both `<example>` blocks from the
rubric instead, and see whether the judge does as well without them.

Keep in mind that these 15 rows aren't a fair test anymore, because you looked at
them to make your change. A better score may only mean you fixed those answers.
It doesn't show how the judge will do on answers it hasn't seen.

**Troubleshooting**

- **The judge's labels look wrong across the board:** The script only reads the
  text between the two `` ``` `` lines, so the file has to have exactly one pair.
  Ask OpenCode to check it.

**Finish with a few notes.** Answer these for yourself:

1. Which evaluator would you trust to stop a new version of the agent from
   shipping, and what evidence would you need first?
2. Which disagreement would you fix first, and why?
3. Did your rubric change improve recall without lowering precision too much?

In Module 4, the agent gets tools that act on a store database, such as looking
up orders and processing refunds. You'll evaluate the steps it takes, not just
its final answer. That lab starts with an empty Phoenix project and records new
traces.



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

Never delete the `phoenix-data` folder. It holds the 57 traces, and
deleting it removes them.

**Task 1: Build the labeled dataframe**

The script OpenCode writes, `build_labeled_df.py`, does roughly this:

```python
spans = Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent")
traces = spans[spans["parent_id"].isna()]  # top-level spans: one per question
traces = traces.rename(columns={
    "attributes.input.value": "input",
    "attributes.output.value": "output",
})[["input", "output", "context.span_id"]]
# labels: one row per question in queries.md, with input, category, and policy
df = traces.merge(labels, on="input", how="inner")
```

The `inner` merge keeps only the questions that are both in Phoenix and in
`queries.md`. That's why your chat questions drop out, and why an edited
line in `queries.md` loses its row.

**Task 2: Prepare and split the dataset**

```python
train_df, test_df = train_test_split(
    labeled, test_size=15, random_state=42, stratify=labeled["policy"]
)
```

**Task 3: Build a code evaluator**

```python
NOT_IN_CATALOG = ["jeans", "blazer", "polo", "tuxedo", "loafers"]

@create_evaluator(name="product_exists", kind="code")
def product_exists(output: str) -> float:
    text = output.lower()
    return 0.0 if any(item in text for item in NOT_IN_CATALOG) else 1.0

results = evaluate_dataframe(dataframe=train_df, evaluators=[product_exists])
```

`item in text` is a substring check, which is why a word can match inside
a longer one. Each result is then saved in Phoenix as an annotation, linked
to its trace by the span ID:

```python
Client().spans.log_span_annotations_dataframe(
    dataframe=annotations,  # columns: span_id, label, score, explanation
    annotator_kind="CODE",
    annotation_name="product_exists",
)
```

Tasks 4 and 5 save their results the same way, with `annotator_kind="LLM"`.

**Task 4: Run a built-in LLM judge**

```python
judge_llm = LLM(provider="anthropic", model="claude-sonnet-5-5")
correctness = CorrectnessEvaluator(llm=judge_llm)
with suppress_tracing():
    results = evaluate_dataframe(dataframe=train_df, evaluators=[correctness])
```

**Task 5: Run a custom LLM judge**

```python
policy_compliance = ClassificationEvaluator(
    name="policy_compliance",
    llm=judge_llm,
    prompt_template=rubric,  # the text between the ``` lines
    choices={"compliant": 1.0, "non_compliant": 0.0},
)
```

The evaluator fills in `{input}` and `{output}` in the rubric with each
row's question and answer. The keys in `choices` are the labels saved in
Phoenix.

**Task 6: Validate the custom judge**

```python
labels = ["non_compliant", "compliant"]
print(classification_report(human_labels, judge_labels, labels=labels, digits=3))
print(confusion_matrix(human_labels, judge_labels, labels=labels))
print(cohen_kappa_score(human_labels, judge_labels))
```

After you edit the rubric, `python3 meta_eval.py` runs the meta-evaluation
again with the rubric as it is now.

**Progress circles**

Each task's progress circle turns green when that task's Data Explorer tab
exists. The prompts name the tabs, from `task1-labeled` to
`task6-meta-eval`.



---
