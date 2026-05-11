# Automated Insights Platform — VS Code + Claude Code Setup

## What This Is

A lightweight, human-in-the-loop analytical workflow that runs inside VS Code using Claude Code. It mimics the behavior of a senior data scientist — guiding problem-solving, accelerating investigation, and producing nuanced insights — while keeping you in control at every key decision point.

The workflow is structured as a series of nodes (EDA, Segmentation, Profiling, Driver Analysis, Insight Synthesis), each pausing for your review and instruction before proceeding. All decisions are written to a persistent state file so analyses can span multiple days without losing context.

---

## Project Structure

```
automated-insights-platform/
├── README.md                          ← you are here
├── orchestrator_instructions.md       ← paste this into Claude Code to start a session
├── intake_template.md                 ← copy this to start a new analysis
├── data_dictionary_template.md        ← copy this to start a new analysis
├── skills/
│   ├── eda_skill.md                   ← EDA node instructions
│   ├── segmentation_skill.md          ← Segmentation node instructions
│   ├── profiling_skill.md             ← Profiling node instructions
│   ├── driver_analysis_skill.md       ← Driver analysis node instructions
│   └── insight_synthesis_skill.md     ← Insight synthesis node instructions
├── sample/
│   ├── sample_intake.md               ← pre-filled example intake
│   └── sample_data_dictionary.md      ← pre-filled example data dictionary
└── analyses/
    └── {analysis_id}/                 ← one folder per analysis, fully self-contained
        ├── intake.md                  ← business question, hypotheses, domain conventions
        ├── state.json                 ← auto-managed state, do not edit manually
        ├── data/
        │   ├── your_dataset.csv
        │   └── data_dictionary.md
        └── outputs/
            └── eda_charts/            ← all generated charts and reports
```

**The `skills/` folder and all root-level files are shared across every analysis and are never duplicated or modified per run.** Only the `analyses/{analysis_id}/` folder is new per analysis.

---

## Prerequisites

- VS Code installed
- Claude Code extension installed and authenticated
- Python 3.8 or above

```bash
pip install pandas numpy scipy scikit-learn plotly kaleido
```

---

## How to Run an Analysis — Step by Step

### Before Your First Run (One Time)

1. Open this project folder in VS Code
2. Install the Python dependencies above
3. Open Claude Code in VS Code (Cmd+Shift+P → Claude Code)
4. Copy the full contents of `orchestrator_instructions.md` and paste into Claude Code — this loads the orchestrator for your session

---

### Starting a New Analysis

**Step 1 — Create the analysis folder**

Under `analyses/`, create a new folder with a descriptive snake_case name that identifies the analysis — for example `credit_card_segmentation` or `retail_customer_lapse`.

Inside it, create:
```
analyses/your_analysis_id/
├── data/
└── outputs/
    └── eda_charts/
```

**Step 2 — Place your dataset**

Copy your CSV into `analyses/your_analysis_id/data/`.

**Step 3 — Fill out the data dictionary**

Copy `data_dictionary_template.md` into `analyses/your_analysis_id/data/` as `data_dictionary.md`. Fill in every column definition, the grain of the data, and any known quirks.

**Step 4 — Fill out the intake file**

Copy `intake_template.md` into `analyses/your_analysis_id/` as `intake.md`. Fill in the business question, point to your CSV and data dictionary, add domain conventions and hypotheses.

**Step 5 — Start the session in Claude Code**

Say to Claude Code:

> "I am starting a new analysis called `your_analysis_id`. Please read the intake file, the data dictionary, and the EDA skill file, then run the EDA node."

The orchestrator will read the correct files for that analysis, initialize state.json, and begin.

---

### Resuming an Analysis

Open Claude Code and say:

> "I am resuming the `your_analysis_id` analysis. Please read the current state and tell me where we are."

Claude Code will read `analyses/your_analysis_id/state.json`, surface all prior decisions and the current node position, and wait for your instruction.

---

### Switching Between Analyses

You can have multiple analyses in progress simultaneously. To switch, just tell Claude Code which analysis to activate:

> "Switch to the `credit_card_segmentation` analysis."

Claude Code reads the state for that analysis and resumes from where you left off. No state bleeds between analyses.

---

### During the Analysis — How Each Node Works

For every node, Claude Code will:

1. Read the relevant skill file from `skills/`
2. Read `analyses/{analysis_id}/intake.md`
3. Read `analyses/{analysis_id}/data/data_dictionary.md`
4. Read `analyses/{analysis_id}/state.json`
5. Execute Python against your CSV
6. Surface findings in plain language with interactive HTML charts
7. Wait for your instruction before proceeding
8. Write your decisions to state.json
9. Move to the next node only when you say "proceed"

---

### Leaving a Note Before You Close

> "Please add this note before I go: [your note]"

Written to the `notes` array in state.json with a timestamp. Surfaced automatically on resume.

---

## Key Design Principles

**Framework and analysis are separated**
Skill files encode universal data science methodology — statistical reasoning, ML concepts, analytical heuristics. They never contain domain-specific language and never change between analyses. Domain context comes from the intake file and data dictionary at runtime, per analysis.

**State as persistent memory**
`state.json` accumulates every decision, finding, and note for one analysis. It is scoped to its analysis folder and never shared across analyses.

**Human-in-the-loop at every node**
The workflow pauses after every node. You review, give your instruction, explicitly say "proceed." The system never moves forward on its own.

**Analyses are isolated, the framework is shared**
Adding a new analysis is three steps: create a folder under `analyses/`, drop in a CSV, fill in the intake and data dictionary. The skills, orchestrator, and templates are untouched.

---

## Iterating and Improving

When a node produces output that falls short of your standard, add the missing reasoning back into the relevant skill file in `skills/`. Every improvement benefits all future analyses automatically — past analyses are unaffected.


## Demo Datasets Used in Development
- Telco Customer Churn — kaggle.com/datasets/blastchar/telco-customer-churn
- Credit Card Customer Segmentation — kaggle.com/datasets/arjunbhasin2013/ccdata
