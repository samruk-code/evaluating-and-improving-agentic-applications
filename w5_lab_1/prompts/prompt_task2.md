<!-- Task 2 — The baseline: six evaluators, two datasets -->
Build the response_grounding judge, then run the baseline experiments. Be concise: write the two files, run the script, print the summaries, don't explain unless something fails.

Write grounding_evaluator.py — later tasks import it, so keep it importable and free of side effects:
- From phoenix.client.experiments import create_evaluator. From evaluators import CARRIED_EVALUATORS, build_judge, judge. From app import format_trajectory.
- grounding_classifier = build_judge("response_grounding", "grounding_prompt.md", {"grounded": 1.0, "ungrounded": 0.0})
- @create_evaluator(kind="LLM", name="response_grounding") async def response_grounding(input, output): if output is falsy, return 0.0, "ungrounded", "task produced no output". Otherwise `score = await judge(grounding_classifier, {"input": input["question"], "trajectory_text": format_trajectory(output["trajectory"]), "output": output["response"]})` and return score.score, score.label and score.explanation as a three-tuple. Use the `judge` helper rather than calling async_evaluate directly — it suppresses tracing around the call and retries the transient connection errors a burst of judge calls produces.
- EVALUATORS = CARRIED_EVALUATORS + [response_grounding]

Write task2_baseline.py:
- import asyncio, pandas as pd. From exp_utils import client, run_experiment_on, experiment_frame, summarise. From grounding_evaluator import EVALUATORS. From datasets_spec import DATASET_NAMES. From df_view import save_view.
- Load both datasets with client.datasets.get_dataset(dataset=DATASET_NAMES[...]).
- In one asyncio.run, await run_experiment_on(failures_ds, "v1", "baseline-v1-failures", EVALUATORS) and then run_experiment_on(known_good_ds, "v1", "baseline-v1-known-good", EVALUATORS).
- Build frames with experiment_frame(ran, dataset, "baseline-v1"), then call summarise(frame, "BASELINE v1 — failure set") and summarise(frame, "BASELINE v1 — known-good set") — summarise prints for itself, so do not wrap it in print().
- Save both frames with to_pickle: base_f.pkl and base_kg.pkl. Later tasks load these. Once this script has succeeded, do not run it again.
- Now the part that matters: print the explanations, not the scores. For every failure-set row print the case, its response_grounding_label, its tools_called, and the first 300 characters of response_grounding_explanation.
- Build a viewable frame from both sets: split, case, question, tools_called joined with ", ", n_tool_calls, latency_s, each code dimension as "pass"/"fail" and each judged dimension as its label. save_view(viewable, title="Task 2 — Baseline v1", subtitle="six evaluators, two datasets", name="task2-baseline").
- When done, print exactly: Baseline scored — grounding G% on the failure set, K% on known-good, printed above. (fill in G and K)
