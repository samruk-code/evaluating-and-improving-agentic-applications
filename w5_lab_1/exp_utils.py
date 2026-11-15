"""Experiment plumbing: run one, flatten it, compare two, price the difference.

None of this is evaluation logic — it is the joining and printing that would
otherwise be re-typed in every task. The interesting decisions (what to change,
what to measure, when to stop) stay in your scripts and in the rubric files.

An experiment is three things: a **dataset**, a **task**, and **evaluators**.
The task is one function that runs the agent on one example; Phoenix calls it
once per example, records what it returns, and hands that to every evaluator.
The task here closes over a prompt version — swapping that version, and nothing
else, is what makes two experiments comparable.
"""

from __future__ import annotations

import pandas as pd
from phoenix.client import AsyncClient, Client
from phoenix.client.experiments import async_run_experiment

import db
from app import ask_agent
from evaluators import DIMENSIONS

client = Client()
async_client = AsyncClient()
_conn = db.get_connection()

# Two projects this module. Anything we run ourselves lands in the first (the
# same project modules 1-4 used); the simulated production traffic lands in the
# second. That split is the offline/online distinction made concrete: offline
# evaluation runs against datasets you control, online evaluation against
# traffic you do not.
#
# Which one a script writes to is decided by `NORTHWIND_PHOENIX_PROJECT` before
# app.py is imported — see the comment on PROJECT_NAME there. There is no
# in-process switch: `openinference.instrumentation.using_project` is not in
# this stack's version, and re-registering mid-process does not move spans
# because the instrumentor already holds its tracer.
#
# Experiments are separate again: Phoenix gives each one its own project named
# after the dataset, which is why the experiment runs in this module do not show
# up under either name below.
OFFLINE_PROJECT = "dlai-ecommerce-agent"
PRODUCTION_PROJECT = "dlai-northwind-production"

# A bar you could apply to the Task 4 table without another experiment.
# On a three-example failure set, 80% means every case must pass (2/3 is 67%).
# Tasks 1–4 do not call check_bar; the shipping decision is read off the
# three-way comparison instead.
BAR = {
    "grounding_failure_set": 0.80,
    "known_good_regressions": 0,
    "extra_calls_per_case": 1.0,
}


# --- datasets --------------------------------------------------------------


def create_or_get(name: str, rows: list, split: str, description: str):
    """Create the dataset, or reuse it if an earlier run already made it.

    `create_dataset` posts action="create", so a second run of the same script
    would fail on the duplicate name. Falling back to `get_dataset` keeps every
    task re-runnable, which matters in a lab where a step can be interrupted.
    """
    from datasets_spec import to_metadata

    try:
        return client.datasets.create_dataset(
            name=name,
            dataset_description=description,
            inputs=[{"question": row["question"]} for row in rows],
            outputs=[{} for _ in rows],
            metadata=[to_metadata(row, split) for row in rows],
        )
    except Exception as error:
        print(f"  '{name}' already exists, reusing it ({type(error).__name__})")
        return client.datasets.get_dataset(dataset=name)


# --- running ---------------------------------------------------------------


def make_task(prompt_version: str):
    """Build the task function for one prompt version."""

    async def run_northwind_agent(input):
        return await ask_agent(input["question"], prompt_version)

    run_northwind_agent.__name__ = f"run_northwind_agent_{prompt_version}"
    return run_northwind_agent


# Phoenix defaults to concurrency=3 and a 60s timeout. Each example here is an
# agent run plus two judge calls, and bursts of those against one API key show
# up as transient connection errors that leave an example unscored — a NaN in
# the frame and a traceback in the middle of a five-minute run. Two at a time
# with a longer timeout is slower and finishes.
EXPERIMENT_CONCURRENCY = 2
EXPERIMENT_TIMEOUT_S = 120


async def run_experiment_on(dataset, prompt_version: str, label: str, evaluators: list):
    """One experiment: this dataset, this prompt version, these evaluators.

    `refunds` is cleared first. It is global state that the outcome evaluator
    reads, so without this an experiment would score itself against rows a
    previous experiment — or somebody's Preview App chat — left behind.

    Note what is *not* here: a `suppress_tracing()` wrapper around the whole
    experiment. Phoenix records each task run as a span of its own, and under
    suppression that span is a NonRecordingSpan the experiment machinery then
    fails on ("'NonRecordingSpan' object has no attribute 'start_time'"), taking
    every run with it. Keeping the judges' own model calls out of the traced
    project is done where those calls happen — inside the evaluators — not out
    here.
    """
    cleared = db.reset_refunds(_conn)
    if cleared:
        print(f"  cleared {cleared} refund row(s) before '{label}'")
    return await async_run_experiment(
        dataset=dataset,
        task=make_task(prompt_version),
        evaluators=evaluators,
        experiment_name=label,
        experiment_metadata={"prompt_version": prompt_version},
        client=async_client,
        print_summary=False,
        concurrency=EXPERIMENT_CONCURRENCY,
        timeout=EXPERIMENT_TIMEOUT_S,
    )


def current_project() -> str:
    """The project this process is writing spans to."""
    from app import PROJECT_NAME

    return PROJECT_NAME


# --- reading the result ----------------------------------------------------


def experiment_frame(ran, dataset, label: str) -> pd.DataFrame:
    """Flatten a RanExperiment into one row per example, one column per evaluator.

    `RanExperiment` is a plain dict holding `task_runs` (one per example, with
    whatever the task returned under `output`) and `evaluation_runs` (one per
    run x evaluator). It carries only a `dataset_id`, not the dataset, so the
    dataset is passed separately to recover each example's `case` and question.
    """
    by_example = {
        ex["id"]: {
            "case": (ex.get("metadata") or {}).get("case"),
            "split": (ex.get("metadata") or {}).get("split"),
            "question": (ex.get("input") or {}).get("question"),
        }
        for ex in dataset.examples
    }

    runs = {}
    for run in ran["task_runs"]:
        out = run.get("output")
        out = out if isinstance(out, dict) else {}
        row = dict(by_example.get(run["dataset_example_id"], {}))
        row["experiment"] = label
        row["error"] = run.get("error")
        row["response"] = out.get("response", "")
        row["tools_called"] = out.get("tools_called", [])
        row["n_tool_calls"] = len(row["tools_called"])
        row["latency_s"] = out.get("latency_s")
        row["prompt_version"] = out.get("prompt_version")
        runs[run["id"]] = row

    for evaluation in ran["evaluation_runs"]:
        row = runs.get(evaluation.experiment_run_id)
        if row is None or evaluation.result is None:
            continue
        results = (evaluation.result if isinstance(evaluation.result, (list, tuple))
                   else [evaluation.result])
        for result in results:
            name = evaluation.name or result.get("name")
            if not name:
                continue
            row[name] = result.get("score")
            row[f"{name}_label"] = result.get("label")
            row[f"{name}_explanation"] = result.get("explanation")

    # A run that errored (or an experiment where every run errored) still has
    # to come back as a frame with the usual columns, or every later join dies
    # with a KeyError instead of showing you what went wrong.
    columns = ["case", "split", "question", "experiment", "error", "response",
               "tools_called", "n_tool_calls", "latency_s", "prompt_version"]
    frame = pd.DataFrame(list(runs.values()), columns=None if runs else columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = None
    for dimension in DIMENSIONS:
        if dimension not in frame.columns:
            frame[dimension] = float("nan")
        for suffix in ("_label", "_explanation"):
            if f"{dimension}{suffix}" not in frame.columns:
                frame[f"{dimension}{suffix}"] = None
    return frame


def summarise(frame: pd.DataFrame, title: str) -> None:
    """Pass rate per dimension. The headline, not the finding."""
    print(title)
    print("-" * len(title))
    for dimension in DIMENSIONS:
        column = frame[dimension].dropna()
        if len(column):
            missing = len(frame) - len(column)
            note = f"   [{missing} unscored]" if missing else ""
            print(f"  {dimension:<24} {column.mean():.0%}  "
                  f"({int(column.sum())}/{len(column)}){note}")
    errored = frame["error"].notna().sum() if "error" in frame.columns else 0
    if errored:
        print(f"  NOTE: {errored} task run(s) errored — those rows are not scored.")
    print()


# --- comparing -------------------------------------------------------------


def compare(before: pd.DataFrame, after: pd.DataFrame, dimension: str, title: str):
    """Per-example before/after on one dimension, in both directions.

    Aggregates tell you something moved. They will happily hide a fix and a
    regression that cancel out, which is why this prints every example.
    """
    left = before[["case", dimension]].rename(columns={dimension: "before"})
    right = after[["case", dimension]].rename(columns={dimension: "after"})
    merged = left.merge(right, on="case", how="outer")

    def verdict(row):
        was, now = row["before"], row["after"]
        if pd.isna(was) or pd.isna(now):
            return "?"
        if was == now:
            return "pass" if now == 1.0 else "fail"
        return "FIXED" if now > was else "REGRESSED"

    merged["change"] = merged.apply(verdict, axis=1)
    print(f"{title}  [{dimension}]")
    print(merged.to_string(index=False))
    fixed = int((merged["change"] == "FIXED").sum())
    broke = int((merged["change"] == "REGRESSED").sum())
    print(f"  -> fixed: {fixed}   regressed: {broke}\n")
    return merged


def three_way(frames: list, dimension: str, title: str):
    """One column per experiment, one row per example."""
    out = None
    for label, frame in frames:
        column = frame[["case", dimension]].rename(columns={dimension: label})
        out = column if out is None else out.merge(column, on="case", how="outer")
    print(f"{title}  [{dimension}]")
    print(out.to_string(index=False))
    print("  means: " + "   ".join(
        f"{label}={frame[dimension].dropna().mean():.0%}"
        for label, frame in frames if frame[dimension].notna().any()))
    print()
    return out


def cost_table(before: pd.DataFrame, after: pd.DataFrame,
               label_before: str, label_after: str) -> pd.DataFrame:
    """What the change cost in tool calls and latency. Adding a step is never free."""
    left = before[["case", "n_tool_calls", "latency_s"]].rename(columns={
        "n_tool_calls": f"calls_{label_before}", "latency_s": f"sec_{label_before}"})
    right = after[["case", "n_tool_calls", "latency_s"]].rename(columns={
        "n_tool_calls": f"calls_{label_after}", "latency_s": f"sec_{label_after}"})
    merged = left.merge(right, on="case", how="outer")
    merged["extra_calls"] = merged[f"calls_{label_after}"] - merged[f"calls_{label_before}"]
    return merged


def check_bar(failure_frame: pd.DataFrame, known_good_frame: pd.DataFrame,
              baseline_known_good: pd.DataFrame, label: str, bar: dict | None = None) -> dict:
    """Score one iteration against the bar that was written down in advance."""
    bar = bar or BAR
    grounding = failure_frame["response_grounding"].dropna().mean()

    regressions = 0
    merged = baseline_known_good[["case"] + DIMENSIONS].merge(
        known_good_frame[["case"] + DIMENSIONS], on="case", suffixes=("_base", "_new"))
    for dimension in DIMENSIONS:
        was, now = merged[f"{dimension}_base"], merged[f"{dimension}_new"]
        regressions += int(((was == 1.0) & (now == 0.0)).sum())

    extra = known_good_frame["n_tool_calls"].mean() - baseline_known_good["n_tool_calls"].mean()

    verdicts = {
        "grounding": grounding >= bar["grounding_failure_set"],
        "regressions": regressions <= bar["known_good_regressions"],
        "cost": extra <= bar["extra_calls_per_case"],
    }
    print(label)
    print(f"  grounding on failure set   {grounding:.0%}   "
          f"bar >= {bar['grounding_failure_set']:.0%}   "
          f"{'PASS' if verdicts['grounding'] else 'MISS'}")
    print(f"  regressions on known-good  {regressions}     "
          f"bar = {bar['known_good_regressions']}       "
          f"{'PASS' if verdicts['regressions'] else 'MISS'}")
    print(f"  extra tool calls per case  {extra:+.2f}  "
          f"bar <= {bar['extra_calls_per_case']}    "
          f"{'PASS' if verdicts['cost'] else 'MISS'}")
    print()
    return {"grounding": grounding, "regressions": regressions,
            "extra_calls": extra, "verdicts": verdicts}
