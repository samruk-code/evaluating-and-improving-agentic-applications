"""Module 4's five evaluators, carried into module 5 unchanged in logic.

That last part matters more than it looks. This module changes the agent and
then asks whether it got better. If the criteria moved at the same time, the
comparison would mean nothing — so these are the same rules module 4 ended
with, and they are given to you rather than rebuilt.

Two things do change, both mechanical:

1. **A different `create_evaluator`.** Module 4 imported it from `phoenix.evals`
   and ran it over a dataframe with `evaluate_dataframe`. Experiments use
   `phoenix.client.experiments.create_evaluator`, which binds arguments by name
   from the dataset example: `input`, `output`, `expected`, `metadata`,
   `example`.
2. **The spec travels with the example.** Module 4's evaluators looked up a
   module-level `QUERY_SPEC` keyed on the query string. Inside an experiment
   that global is the wrong home for it, so the spec rides in `metadata` and the
   evaluators read it from there.

`output` is whatever the experiment's task returned — here, `ask_agent`'s dict:
`response`, `trajectory`, `tools_called`, `latency_s`, `prompt_version`.

The sixth evaluator, `response_grounding`, is yours to build. `build_judge`
below is the same wiring `policy_compliance` uses, so it is a rubric file and
three lines.
"""

from __future__ import annotations

import asyncio
import re

from openinference.instrumentation import suppress_tracing
from phoenix.client.experiments import create_evaluator
from phoenix.evals import LLM, ClassificationEvaluator

import db

JUDGE_MODEL = "claude-sonnet-5-5"

# One connection for the whole scoring process, to the same northwind.db the
# agent app writes to. The outcome evaluator asks this file what happened
# instead of trusting the trajectory or the agent's own words.
_conn = db.get_connection()


def _spec(metadata: dict | None) -> dict:
    """Normalise an example's metadata into the spec the evaluators expect."""
    metadata = metadata or {}
    return {
        "expected_tools": set(metadata.get("expected_tools") or []),
        "expected_args": metadata.get("expected_args") or {},
        "expected_refund": metadata.get("expected_refund"),
        "requires_identity_first": bool(metadata.get("requires_identity_first")),
        "product_id": metadata.get("product_id"),
    }


# --- code evaluators -------------------------------------------------------


@create_evaluator(kind="CODE", name="tool_selection")
def tool_selection(output, metadata):
    """Did the tools that had to fire, fire?

    Loose on route, strict on the critical steps: extra calls are allowed, a
    missing required one is not.
    """
    if not output:
        return 0.0
    spec = _spec(metadata)
    if not spec["expected_tools"]:
        return 1.0
    return 1.0 if spec["expected_tools"].issubset(set(output["tools_called"])) else 0.0


@create_evaluator(kind="CODE", name="tool_invocation")
def tool_invocation(output, metadata):
    """Did each tool receive the arguments the query implied?

    A tool that never fired is selection's problem, not invocation's — this is
    the evaluator that catches a fluent, successful-looking lookup of the
    *wrong* order or the wrong product.
    """
    if not output:
        return 0.0
    for tool_name, expected in _spec(metadata)["expected_args"].items():
        calls = [c for c in output["trajectory"] if c["tool"] == tool_name]
        if not calls:
            continue
        for key, want in expected.items():
            got = str(calls[0]["args"].get(key, "")).strip().upper()
            if got != str(want).strip().upper():
                return 0.0
    return 1.0


@create_evaluator(kind="CODE", name="outcome")
def outcome(output, metadata):
    """Did this run leave the refunds table in the state it should have?

    Not the trace, not the agent's words — one SQL query against the table the
    money actually moves through. Two reviewers could never disagree.
    """
    if not output:
        return 0.0
    expected = _spec(metadata)["expected_refund"]
    refunded_here = [c for c in output["trajectory"] if c["tool"] == "process_refund"]

    if expected is None:
        # This run should not have moved any money.
        return 0.0 if refunded_here else 1.0

    if not refunded_here:
        return 0.0
    rows = [dict(r) for r in _conn.execute("SELECT * FROM refunds")]
    match = [
        r for r in rows
        if r["order_id"] == expected["order_id"]
        and abs(r["amount"] - expected["amount"]) < 0.01
    ]
    return 1.0 if match else 0.0


@create_evaluator(kind="CODE", name="identity_before_refund")
def identity_before_refund(output, metadata):
    """Deterministic sequencing rule — no model required."""
    if not output:
        return 0.0
    if not _spec(metadata)["requires_identity_first"]:
        return 1.0
    called = output["tools_called"]
    if "process_refund" not in called:
        return 1.0  # no refund attempted, rule not engaged
    if "get_customer" not in called:
        return 0.0
    return 1.0 if called.index("get_customer") < called.index("process_refund") else 0.0


# --- LLM judges ------------------------------------------------------------

_FENCE = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)

# The three fields every rubric in this course is handed. Anything else in
# braces is data, not a placeholder — see `_escape_braces`.
PLACEHOLDERS = ("input", "trajectory_text", "output")


def _escape_braces(template: str) -> str:
    """Protect JSON in a rubric's worked examples from the template engine.

    `ClassificationEvaluator` renders its template with f-string semantics, so a
    literal `{"order_id": "4521"}` in a worked example is read as a variable
    called `"order_id"` and the render dies with `Path not found`. Rubrics are
    meant to be *edited* — by you, in the browser editor, mid-lab — so the fix
    belongs here rather than in a rule you have to remember: every brace is
    doubled (which renders as a literal brace), then the three real
    placeholders are put back.

    The consequence worth knowing: `{something_else}` in a rubric renders as
    literal text, not as a variable. To add a field to a judge, add it to
    PLACEHOLDERS and pass it in the payload.
    """
    escaped = template.replace("{", "{{").replace("}", "}}")
    for name in PLACEHOLDERS:
        escaped = escaped.replace("{{%s}}" % name, "{%s}" % name)
    return escaped


def load_rubric(path: str) -> str:
    """Pull the judge prompt out of a rubric markdown file.

    The prose around it is for you; the single fenced block is what the model
    sees. Keeping both in one file is what makes the Edit button useful — you
    read why a line is there and change it in the same place.
    """
    text = open(path).read()
    blocks = _FENCE.findall(text)
    if len(blocks) != 1:
        raise ValueError(
            f"{path}: expected exactly one ``` fenced block, found {len(blocks)}"
        )
    return _escape_braces(blocks[0].strip())


def build_judge(name: str, rubric_path: str, choices: dict) -> ClassificationEvaluator:
    """A ClassificationEvaluator over a rubric file, as in modules 3 and 4."""
    return ClassificationEvaluator(
        name=name,
        llm=LLM(provider="anthropic", model=JUDGE_MODEL),
        prompt_template=load_rubric(rubric_path),
        choices=choices,
    )


JUDGE_ATTEMPTS = 3
JUDGE_BACKOFF_S = 2.0


async def judge(classifier: ClassificationEvaluator, payload: dict):
    """Run a judge, retrying transient API failures.

    An experiment scores every example with every evaluator, so a batch is a
    burst of model calls against one API key. A single dropped connection would
    otherwise surface as `RuntimeError: evaluator failed for example id ...`,
    leaving one cell of the frame empty (NaN) and a traceback in the middle of a
    five-minute run — which reads like a bug in your evaluator rather than a
    network blip. Three tries with a short backoff makes that a pause instead.

    Tracing is suppressed around the call: a judge grading the agent is not part
    of the agent's trace. Note that phoenix.evals still traces its own
    evaluation spans to a project called `evaluators` — that is where to look if
    you want to see what a judge was actually sent. Do not move this suppression
    out to wrap the experiment itself: Phoenix records each task run as a span,
    and a suppressed span breaks the experiment with a NonRecordingSpan error.
    """
    last_error = None
    for attempt in range(1, JUDGE_ATTEMPTS + 1):
        try:
            with suppress_tracing():
                return (await classifier.async_evaluate(payload))[0]
        except Exception as error:  # noqa: BLE001 — any transport failure is retryable here
            last_error = error
            if attempt < JUDGE_ATTEMPTS:
                await asyncio.sleep(JUDGE_BACKOFF_S * attempt)
    raise last_error


# Module 4's rubric, unchanged. Its data block is the trajectory, not the
# answer: it judges whether the agent followed policy while *acting*.
policy_classifier = build_judge(
    "policy_compliance",
    "policy_compliance_prompt.md",
    {"compliant": 1.0, "non_compliant": 0.0},
)


@create_evaluator(kind="LLM", name="policy_compliance")
async def policy_compliance(input, output):
    if not output:
        return 0.0, "non_compliant", "task produced no output"
    from app import format_trajectory

    score = await judge(policy_classifier, {
        "input": input["question"],
        "trajectory_text": format_trajectory(output["trajectory"]),
        "output": output["response"],
    })
    return score.score, score.label, score.explanation


# The five module 4 ended with. Task 2 adds the sixth.
CARRIED_EVALUATORS = [
    tool_selection,
    tool_invocation,
    outcome,
    identity_before_refund,
    policy_compliance,
]

DIMENSIONS = ["tool_selection", "tool_invocation", "outcome",
              "identity_before_refund", "policy_compliance", "response_grounding"]
