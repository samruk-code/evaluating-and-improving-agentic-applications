# Module 2, Lab 1: Task guide

Start with [README.md](README.md) to set up your local environment.

These tasks refer to the course interface. Locally, open Phoenix at http://localhost:6006 and the chat app at http://localhost:7860. Give the linked prompt files to your coding assistant, or write your own. The prompts are guides; adapt them freely to meet each task's goal. Saved edits from the lab are already in `prompts/`. The wording you started from is in `prompts/original/`.

### Task 1: Create a dataframe to analyze the traces

**Goal:** Put the agent's traces into a table, with one row per question.

The later tasks work with the questions and answers in Python, so they need
them in a table. In Python, a table like this is called a **dataframe**. You'll
use the same steps in later tasks to pull in the agent's answers to new
questions.

Phoenix saves each step of a question as a separate span: the whole request
(`ask_agent`), the catalog search, each inventory check, and the model call. So
when the prompt pulls the spans from Phoenix, each question shows up as several
rows. Only the `ask_agent` row holds both the customer's question and the
agent's final answer. So the prompt keeps only those rows, which leaves one row
per question.

1. Send this prompt to OpenCode, which will:
   - get every span in the `dlai-ecommerce-agent` project from Phoenix
   - keep only the top-level spans, one for each question
   - keep three columns: the question, the answer, and the span's ID
   - save the table so you can see it in **Data Explorer**

   When OpenCode prints `Dataframe saved — 15 rows`, it's done. If you've done
   this lab before, you'll see more rows.

[Open this task's prompt](prompts/prompt_task1.md)

2. Click the **Data Explorer** button at the top right of the lab, then click
   **Refresh** at the top right of Data Explorer. If you don't click
   **Refresh**, you won't see the new table. Check that the table has 15 rows
   and these three columns:
   - `input`: the customer's question
   - `output`: the agent's answer
   - `context.span_id`: the span's ID, which links the row back to its trace in
     Phoenix

### Troubleshooting

If the table is empty or has the wrong number of rows, try these:

- Check that Phoenix shows the 15 traces. If it doesn't, see **Troubleshooting**
  under **Before you begin**.
- If you edited the prompt, check that the project name is still exactly
  `dlai-ecommerce-agent`. Names are case-sensitive.
- If the count is wrong but there's no error, the script may have kept every
  span except the top-level ones. Ask OpenCode to check that it keeps the rows
  where `parent_id` is empty.
- If **Data Explorer** says there's no dataframe yet, click **Refresh** at the
  top right of Data Explorer.
- To check it yourself, see **Task 1** under **Working in the terminal** at the
  end of the tasks.





### Task 2: Expand the query set

**Goal:** Add 4 questions to `queries.md`, then have the agent answer all of
them.

The table you made in Task 1 has Module 1's 15 questions. Those were a general
mix, to see how the agent answers different kinds of questions. `queries.md` is
a new, separate list of 17 test questions that comes with this lab. Each one is
chosen on purpose to check something specific the agent can get wrong, such as
inventing a product or making up a returns policy. To see the 17 questions
before you start, ask OpenCode: "Show me the questions in queries.md."

In this task, you'll write 4 questions of your own and add them to
`queries.md`. Then the agent answers all 21 questions in the file. Phoenix
records each answer as a new trace, as it did in Module 1, and the prompt
rebuilds your Task 1 table with every trace: Module 1's 15 plus these 21, for
36 rows.

`queries.md` has seven sections, and each section tests one kind of question:

| Section | What it tests |
|---|---|
| Baseline | Plain questions the catalog fully answers, such as the price of the Chino Pants. The agent should get these right. |
| Hallucination bait | Items that sound right for this store but aren't in the catalog, such as a cashmere scarf. Does the agent invent them? |
| Faithfulness drift | Details the catalog doesn't give, such as whether the Denim Jacket is machine washable. Does the agent answer from general knowledge instead? |
| Scope violations | Topics the agent has no data for, such as gift wrapping or discount codes. Does it make up a policy? |
| Consistency tests | One open-ended question, about what to pack for a rainy camping trip, asked three times, word for word. Are the three answers organized the same way? |
| Multi-part | Two or more requests in one message, such as swim trunks and a beanie. Does the agent drop one? |
| Odd phrasing | Typos, slang, and fragments, such as "flannel pls". Does the agent still understand? |

Three of the sections, Hallucination bait, Faithfulness drift, and Scope
violations, are named for kinds of failure you'll label in Task 3.

You'll add one question each to Hallucination bait, Faithfulness drift, Scope
violations, and Multi-part.

**Tip:** Write questions the way real customers do: vague, slangy, or asking two
things at once, not just clean product lookups. To see what Northwind sells, ask
OpenCode about `catalog.json`, the product catalog. Your Faithfulness drift and
Multi-part questions should ask about products Northwind sells. For a
hallucination bait question, have OpenCode check that your item isn't in the
catalog.

1. Click **Edit queries.md** below and add your 4 questions. Put each one
   on its own line, starting with `- `, under its section's heading, like the
   questions already there. Don't rename the headings or change the questions
   already in the file. The later tasks look for them by their exact text.
   Click **Save**.

   **Note:** Try writing the 4 questions yourself. Deciding what's worth
   testing is the skill this task practices. If you're stuck, you can ask
   OpenCode to suggest a question for each of the four sections, then add the
   ones you like to `queries.md`.

2. Send this prompt to OpenCode, which will:
   - find every question in `queries.md` and count them by section
   - have the agent answer each question, one at a time, skipping any that
     Phoenix already has a trace for
   - rebuild the Task 1 table with every trace, and show it in **Data
     Explorer**

   It takes about 5–7 minutes. When OpenCode prints
   `Query bank run — 21 new queries, 36 total traces in Phoenix`, it's done. If
   you added extra questions, your numbers are higher.

[Open this task's prompt](prompts/prompt_task2.md)

3. Click **Data Explorer**, then click **Refresh**, and check that the table
   has 36 rows: the 15 traces you started with, plus the 21 questions from
   `queries.md`.

### Troubleshooting

If the run stops before OpenCode prints its message, send the same prompt
again. It skips the questions Phoenix already has and continues with the rest.
If Phoenix then shows more than 36 traces, that's fine. A rerun can trace a
question twice, and the later tasks still work. Don't delete traces or the
`phoenix-data` folder to start over.

If OpenCode found fewer questions than you wrote, try these:

- Check that you clicked **Save** in the editor.
- Check that each question is on its own line, starts with `- `, and sits
  under one of the seven headings.
- If some questions got an error instead of an answer, ask OpenCode to look at
  the errors in the run's output. A stray quotation mark or an empty line in
  `queries.md` is a common cause.
- To check it yourself, see **Task 2** under **Working in the terminal** at the
  end of the tasks.





### Task 3: Categorize the failures

**Goal:** Evaluate some of the agent's answers by hand, and save them in Phoenix.

In Task 2, the agent answered the 21 questions in `queries.md`: the 17 that came
with the file and the 4 you wrote. In this task, you'll evaluate 7 of those
answers yourself, to see what it's like to judge the agent's answers by hand.
OpenCode evaluates 7 more, so you have more labeled answers to count.

1. Send this prompt to OpenCode, which will:
   - pick 14 questions: 10 that were already in `queries.md`, and the 4 you
     added
   - write each question and the agent's answer to it into a worksheet,
     `labels.md`
   - leave the first 7 entries blank for you, and label the other 7 itself,
     including your 4 questions

   The prompt picks the questions for you, so don't edit it. When OpenCode
   prints `labels.md created — 14 queries, 7 left for you to fill in`,
   it's done. If you added extra questions in Task 2, the first number may be
   higher. You still label only the first 7.

[Open this task's prompt](prompts/prompt_task3_worksheet.md)

2. Now that OpenCode has created `labels.md`, the worksheet you'll fill in,
   here's how to label. For each of your 7 answers, you'll write down two labels: a **category** and
   a **severity**. The category is either `pass` or
   the kind of mistake the agent made:

   - **pass:** the agent handled it correctly.
   - **hallucination:** it said Northwind has a product, price, color, or size
     that isn't in the catalog, such as offering a cashmere scarf.
   - **faithfulness_drift:** it added details about a real product that the
     catalog doesn't give, such as care instructions or fit. For example, the
     catalog says the merino wool sweater is machine washable on a wool cycle. If
     the agent also says you can tumble dry it, that's faithfulness drift.
   - **scope_violation:** it answered a question it has no data for, such as
     shipping or returns, instead of saying it can't help. For example, in one of
     the 15 traces you started with, a customer asked for a phone number, and the
     agent told them to visit northwindapparel.com, a website it knows nothing
     about.
   - **reasoning_error:** it had the right data but used it wrong, such as saying
     the Slip-On Canvas is in stock when the stock check shows none left.
   - **format_inconsistency:** the same question, asked more than once, got
     answers organized in noticeably different ways.

   If more than one category fits, pick the one that best explains why the
   answer is wrong. Label what the answer says, not what the question was
   written to bring out. Plenty of answers will pass.

   The severity is **low**, **medium**, or **high**, based on how much harm the
   mistake could do. Use **n/a** for a pass.

3. Click **Edit labels.md** below. For each of the first 7 entries, read the
   `answer:` line and fill in `category` and `severity`, for example
   `category: pass` and `severity: n/a`. Click **Save** when you're done.

   Don't change the `query:` or `answer:` lines, because the next prompt finds
   each question's trace by its exact text. Leave the 7 entries OpenCode
   labeled as they are.

   The question about packing for a rainy camping trip appears three times,
   once for each time it was asked. Compare all three answers, including the
   one OpenCode labeled. If they're organized in noticeably different ways,
   label yours `format_inconsistency`.

   **Note:** Try labeling your 7 answers yourself. Judging answers by hand is
   the skill this task practices. If you're stuck, you can ask OpenCode to
   suggest labels for your 7 entries, then check each one before you save.

4. Send this prompt to OpenCode, which will:
   - read the labels in `labels.md`, and stop if any entry is still blank
   - match each question to its trace in Phoenix
   - print the number of answers in each category, and a table of the failures
     by category and severity
   - save the labeled table so you can see it in **Data Explorer**
   - save the failures in Phoenix, as a dataset named
     `ecommerce-agent-v2-manual`

   When OpenCode prints `Manual dataset saved — N failures across M categories`,
   with your numbers in place of N and M, it's done. If OpenCode shows only part
   of its reply, click it in the terminal to expand it.

[Open this task's prompt](prompts/prompt_task3_labeled-dataset.md)

5. Click **Data Explorer**, then click **Refresh**, to see the labeled table.
6. To see the failures you saved, click **Check Phoenix**, then click **Datasets &
   Experiments** in the sidebar, and open `ecommerce-agent-v2-manual`. A
   **dataset** is a table that Phoenix keeps. Each row, called an **example**,
   is one of your failures, with its question, answer, category, and severity.

The counts OpenCode printed show how often each kind of failure came up. A
failure that happens often isn't always the one that matters most. Answers
organized in different ways might come up often, but that's usually low
severity. An invented shipping time might come up once, but it's high severity,
because a customer might act on it. To decide what to fix first, weigh both how
often a failure happens and how much harm it could do.

### Troubleshooting

If the message in step 1 shows fewer than 14 queries, you may have missed a
section in Task 2. Fix this before you label anything, because sending the
step 1 prompt again replaces `labels.md` and its labels. Add the missing
question to `queries.md`, send the Task 2 prompt again to run it, then send the
step 1 prompt again.

If the prompt in step 4 lists unlabeled questions and stops, it saved nothing.
Fill in those entries in `labels.md`, click **Save**, and send the prompt again.

If fewer rows come through than you expected, a `query:` line in `labels.md` was
probably changed. It has to match the question in `queries.md` exactly. Change
it back and send the prompt again.





### Task 4: Generate synthetic test data

**Goal:** Have an LLM write new test questions, then evaluate the agent's
answers to them by hand.

**Synthetic** questions are test questions written by an LLM. They're useful
because an LLM can quickly write many questions, in styles you might not think
of, from formal to slangy to frustrated.

In this task, an LLM writes 21 questions. You'll keep the 7 most worth testing,
have the agent answer them, and evaluate its answers, as in Task 3. Do the four
parts in order.

---

### Task 4-A: Generate

**Goal:** Have an LLM write 21 new customer questions.

1. Send this prompt to OpenCode, which will:
   - write and run a script that asks an LLM for 21 customer questions
   - save the questions in `synthetic_queries_raw.md`, one per line

   The prompt asks the LLM to vary the questions in six ways: how formal they
   are, what the customer wants, how complicated they are, spelling and
   grammar, the customer's mood, and whether the agent has the data to answer.
   Without that, an LLM tends to write the same few obvious questions.

   When OpenCode prints `Generated 21 synthetic queries`, it's done. The LLM
   sometimes writes a few more or fewer questions than it's asked for, so your
   number may be slightly different.

[Open this task's prompt](prompts/prompt_task4a.md)

### Troubleshooting

If you got far fewer than 21 questions, the LLM's reply may have been cut off by
its length limit. Check whether the last question stops mid-sentence. You can
keep the shorter list, since you'll keep only 7, or ask OpenCode to raise the
length limit, `max_tokens`, in `generate_synthetic.py` and run it again.



---

### Task 4-B: Curate

**Goal:** Pick 7 of the LLM's questions to test.

The LLM's 21 questions are in `synthetic_queries_raw.md`. In 4-C, the agent
answers only the questions in a second file, `synthetic_queries.md`. So you'll
pick 7 questions and put them in that file.

1. Decide what makes a question worth keeping:
   - Keep a mix of styles and topics.
   - Keep questions the agent has no data for, such as shipping, returns, or
     exchanges. They test what it does when it can't answer.
   - Keep the ones that surprise you.
   - Drop questions that repeat each other or a question in `queries.md`.
   - Drop anything a clothing store's customer wouldn't ask.
   - For at least 3 of your 7, you should be able to say which category from
     Task 3 you expect them to fail with.
2. Click **Edit synthetic_queries_raw.md** below, then click **Copy all** at the
   top of the editor. Close the editor.

   3. Click **Edit synthetic_queries.md** below and paste the questions under the
   `## Curated synthetic queries` heading. Delete the `## Raw generated queries`
   line that came with them. Then delete every question you don't want to keep.
   The file already has one example question. Keep it or delete it, as long as
   you end up with 7 questions. Click **Save**.

   **Note:** Try choosing the 7 yourself. Deciding which questions are worth
   testing is the skill you're practicing here. If you're stuck, there's a
   shortcut in the dropdown below.

### Optional shortcut: have OpenCode pick 7 for you

Use this instead of steps 2 and 3. Send this prompt to OpenCode, which will
read the LLM's 21 questions, drop duplicates and anything off-topic, and write
7 varied ones into `synthetic_queries.md`, replacing what's there. Then click
**Edit synthetic_queries.md** and check each question it picked.

[Open this task's prompt](prompts/prompt_task4b_optional-draft.md)



---

### Task 4-C: Categorize

**Goal:** Have the agent answer your 7 synthetic questions, then evaluate its
answers yourself.

You now have 7 questions in `synthetic_queries.md`. The agent answers them, and
you label each answer with a category and a severity, the same way you did in
Task 3. This time, you label all 7 yourself.

1. Send this prompt to OpenCode, which will:
   - have the agent answer each question in `synthetic_queries.md`, one at a
     time, skipping any that Phoenix already has a trace for
   - rebuild the Task 1 table with every trace, and show it in **Data
     Explorer**

   It takes a minute or two. When OpenCode prints
   `Synthetic batch run — 7 queries, 43 total traces in Phoenix`, it's done. If
   you have extra traces from earlier tasks, the total is higher.

[Open this task's prompt](prompts/prompt_task4c_run-batch.md)

2. Send this prompt to OpenCode, which will write a worksheet, `task4c.md`,
   with an entry for each of your 7 questions: the question, the agent's
   answer, and blank `category` and `severity` lines.

   When OpenCode prints `task4c.md created — 7 queries, ready for you to label`,
   it's done.

[Open this task's prompt](prompts/prompt_task4c_worksheet.md)

3. Click **Edit task4c.md** below. Each entry has the question and the agent's
   answer, so you can label without opening another view. For every entry, read
   the `query:` and `answer:` lines and fill in `category` and `severity`, using
   the categories from Task 3. Label what each answer says, including answers
   that pass. For example, if the agent describes a returns or delivery process
   it has no data for, that's a `scope_violation`, and often a high-severity
   one. Don't change the `query:` or `answer:` lines. Click **Save**.

   **Note:** Try labeling the 7 answers yourself. If you're stuck, there's a
   shortcut in the dropdown below.

### Optional shortcut: have OpenCode label the answers for you

Send this prompt to OpenCode, which will read each answer and fill in a
category and severity for every blank entry in `task4c.md`. Then click **Edit
task4c.md** again, check each label against the answer, and change any you
disagree with.

[Open this task's prompt](prompts/prompt_task4c_optional-first-pass-labels.md)



4. Send this prompt to OpenCode, which will:
   - read your labels from `task4c.md`, and stop if any entry is still blank
   - match each question to its trace in Phoenix
   - print the number of answers in each category
   - save the labeled table so you can see it in **Data Explorer**

   When OpenCode prints `Synthetic labels applied — N failures across M categories`,
   with your numbers in place of N and M, it's done.

[Open this task's prompt](prompts/prompt_task4c_labeled-dataframe.md)

Compare the categories with the ones from Task 3. Finding failures your Task 3
questions didn't turn up is the point of generating questions, not just having
more of them.

If every answer passes, your questions may have been too easy for the agent. To
try harder ones, add 2–3 questions to `synthetic_queries.md` and send the
prompt in step 1 again. Then add an entry for each new question to `task4c.md`
yourself, with the query, the agent's answer, and blank category and severity
lines like the others, and label it. Don't send
the prompt in step 2 again, because it would replace `task4c.md` with blank
labels.

### Troubleshooting

If the prompt in step 1 stops before OpenCode prints its message, send it
again. It skips the questions Phoenix already has.

If the prompt in step 4 lists unlabeled questions and stops, it saved nothing.
Fill in those entries in `task4c.md`, click **Save**, and send the prompt again.

If rows go missing, a `query:` line in `task4c.md` doesn't match its question
in `synthetic_queries.md` exactly. Change it back and send the prompt again.



---

### Task 4-D: Confirm and save

**Goal:** Check that your Task 4 files are complete and match each other.

If you did 4-A to 4-C in order, this is a quick check before Task 5.

1. Send this prompt to OpenCode, which will:
   - check that `synthetic_queries_raw.md`, `synthetic_queries.md`, and
     `task4c.md` all exist and aren't empty
   - check that every question in `synthetic_queries.md` has a labeled entry in
     `task4c.md`
   - print how many failures you labeled, by category
   - save the labeled table again, so you can see it in **Data Explorer** after
     you click **Refresh**

   When OpenCode prints
   `Synthetic pipeline confirmed — N labeled failures ready for the final benchmark`,
   with your number in place of N, it's done.

[Open this task's prompt](prompts/prompt_task4d.md)

### Troubleshooting

If OpenCode lists a question that doesn't match, `synthetic_queries.md` was
changed after `task4c.md` was made. Either undo that change, or update the
matching `query:` line in `task4c.md`, then send the prompt again.

If it lists entries that are still blank, fill them in, click **Save**, and send
the prompt again.





### Task 5: Build the final benchmark

**Goal:** Combine the failures from Tasks 3 and 4 into one dataset in Phoenix.

This dataset is your benchmark. It holds every failure you found, with its
category, severity, and a link to its trace. When the agent changes, you can
run the same questions again and check whether those failures are fixed.

1. Send this prompt to OpenCode, which will:
   - combine your labeled answers from Task 3 and Task 4
   - keep only the failures, and mark where each one came from: `manual` for
     the questions in `queries.md`, and `synthetic` for the ones the LLM wrote
   - print the failures by category, and by where they came from
   - save them in Phoenix as a dataset named `ecommerce-agent-v2-labeled`

   When OpenCode prints
   `Final benchmark saved — N failures across M categories, from P manual + Q synthetic queries`,
   with your numbers, it's done.

[Open this task's prompt](prompts/prompt_task5.md)

2. Click **Data Explorer**, then click **Refresh**, to see the combined table of
   failures.
3. To see the dataset, click **Check Phoenix**, then click **Datasets & Experiments**
   in the sidebar, and open `ecommerce-agent-v2-labeled`.

**Finish with a few questions**

Answer these for yourself:

1. Which mattered more for deciding what to fix first: the failure that
   happened most often, or the most severe one? Why?
2. Which generated questions did you drop in Task 4-B, and why?
3. If the agent changed tomorrow, which questions in your benchmark would you
   run first?

Labeling by hand doesn't scale, and two people can label the same answer
differently. In the Module 3 lab, you'll start from a prepared benchmark like
this one, and build evaluators that label the answers for you.



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

Never delete the `phoenix-data` folder. It holds the lab's traces, including
the 15 you start with, and deleting it removes them.

**Task 1: Create a dataframe to analyze the traces**

The script OpenCode writes, `dataframe_pull.py`, does roughly this:

```python
from phoenix.client import Client
from df_view import save_view

spans = Client().spans.get_spans_dataframe(project_identifier="dlai-ecommerce-agent")
df = spans[spans["parent_id"].isna()]  # top-level spans only: one row per question
df = df.rename(columns={
    "attributes.input.value": "input",
    "attributes.output.value": "output",
})
df = df[["input", "output", "context.span_id"]]
save_view(df, title="Task 1 — Traces", subtitle=f"{len(df)} agent runs")
```

`isna()` keeps the rows where `parent_id` is empty. Swapping in `notna()`
keeps every *other* span instead, which gives a wrong count without any
error. Keep the title exactly `Task 1 — Traces`: the lab's progress circles
look for it.

**Task 2: Expand the query set**

- Count the questions in `queries.md`: `grep -c '^- ' queries.md`. That
  should be 21, or more if you added extras.
- The script reads each section of `queries.md`, skips any question that's
  already a trace in Phoenix, and sends the rest to the agent one at a
  time. Then it saves all the traces to **Data Explorer** with the title
  `Task 2 — All traces`, which the progress circles also look for.

**Task 3: Categorize the failures**

The key steps in `label_failures.py`:

```python
spans = spans.sort_values("start_time", ascending=False).drop_duplicates("input")
labeled = spans.merge(labels, on="input", how="inner")  # drops the questions labels.md doesn't have
labeled["source"] = "manual"
failures = labeled[labeled["category"] != "pass"]
```

- `drop_duplicates` keeps only the latest trace of each question, in case a
  rerun traced some twice.
- The `inner` merge keeps only questions that appear in both the traces and
  `labels.md`. That's why the 15 traces you started with drop out, and why an
  edited `query:` line loses its row.

The failures are then saved as a Phoenix dataset:

```python
Client().datasets.create_dataset(
    name="ecommerce-agent-v2-manual",
    dataframe=failures[["input", "output", "category", "severity", "source", "context.span_id"]],
    input_keys=["input"],
    output_keys=["output"],
    metadata_keys=["category", "severity", "source"],
    span_id_key="context.span_id",
    dataset_description="Manually categorized failures on the expanded query set.",
)
```

`span_id_key` links each example in the dataset to the span it came from,
so the dataset stays connected to the original traces.

**Task 4: Generate synthetic test data**

- `generate_synthetic.py` calls Claude directly with the `anthropic`
  package. It doesn't go through the agent, so it doesn't create traces.
- Count the generated questions: `grep -c '^- ' synthetic_queries_raw.md`
- Count the ones you kept: `grep -c '^- ' synthetic_queries.md`. That
  should be 7.

**Task 5: Build the final benchmark**

`final_benchmark.py` reuses the labeling steps from Tasks 3 and 4, then
combines them:

```python
combined = pd.concat([manual, synthetic], ignore_index=True)
failures = combined[combined["category"] != "pass"]
```

It saves the failures as the dataset `ecommerce-agent-v2-labeled`, the same
way as in Task 3.



---
