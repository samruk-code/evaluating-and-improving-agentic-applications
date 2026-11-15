# Evaluating and Improving Agentic Applications

This repository contains a multi-part curriculum and lab series focused on building, evaluating, and improving agentic applications. It combines hands-on notebooks, local lab environments, and example agent projects centered on a retail assistant for Northwind Apparel.

The content is organized as a set of independent modules, each with its own instructions, dataset, prompts, and supporting code. Rather than a single application, this repo is a collection of exercises and assignments for learning how to evaluate agent behavior, improve prompts, and reason about tooling, retrieval, and observability.

## Repository structure

- `Assignment_w1/` through `Assignment_w5/`
  - Each folder contains a course assignment with a notebook and a copy of the `apparel-shop-agent` project.
  - These assignments focus on building and testing an agentic shopping assistant with tools, deterministic behaviors, and evaluation logic.

- `w1_lab_1/`, `w1_lab_2/`, `w2_lab_1/`, `w3_lab_1/`, `w4_lab_1/`, `w5_lab_1/`
  - These are standalone lab downloads or exercise folders used for local experimentation.
  - They include prompts, app code, data files, and instructions for running interactive tasks and evaluations.

## What this repo covers

- Agent design and tool use
- Prompt engineering and prompt iteration
- Retrieval- and data-grounded workflows
- Evaluation of agent behavior and trajectory quality
- Policy compliance and observability
- Local experimentation with LLM-backed and deterministic agents

## Quick start

Most folders in this repo are designed to be opened and used independently. In general:

1. Choose a lab or assignment directory.
2. Read that folder's `README.md` or `instructions.md`.
3. Create a Python virtual environment.
4. Install dependencies from that folder's `requirements.txt`.
5. Run the app, evaluation script, or notebook described in the instructions.

Example:

```bash
cd Assignment_w1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the folder is a lab with an app, follow the specific setup steps in that folder's README.

## Example project focus

The Northwind Apparel agent is a recurring example used throughout the repo. It models a clothing store with:

- product catalog and inventory data
- cart and order workflows
- customer support actions
- tool-based agent interactions
- evaluation cases and expected trajectories

## Notes

- This repository is educational and exploratory.
- Some folders are assignment snapshots; others are lab working directories.
- Each subfolder is intended to be treated as its own mini-project.

For the most accurate instructions, always follow the README in the specific folder you want to run.
