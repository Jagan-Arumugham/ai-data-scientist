"""
new_analysis.py — Automated Insights Platform
Run this script to set up a new analysis folder with the correct structure
and an initialized state.json.

Usage:
    python new_analysis.py

You will be prompted for:
    - analysis_id       : a short snake_case name for the analysis
    - business_question : the core question this analysis must answer
    - csv_filename      : the name of your CSV file (just the filename, not the path)
    - nodes_to_skip     : optional — any nodes to skip and why

The script creates:
    analyses/{analysis_id}/
    analyses/{analysis_id}/intake.md       (copied from intake_template.md)
    analyses/{analysis_id}/state.json      (initialized with your inputs)
    analyses/{analysis_id}/data/           (place your CSV and data_dictionary.md here)
    analyses/{analysis_id}/outputs/
    analyses/{analysis_id}/outputs/eda_charts/
"""

import json
import os
import shutil
from datetime import datetime

FRAMEWORK_ROOT = os.path.dirname(os.path.abspath(__file__))
ANALYSES_DIR = os.path.join(FRAMEWORK_ROOT, "analyses")
INTAKE_TEMPLATE = os.path.join(FRAMEWORK_ROOT, "intake_template.md")
DATA_DICT_TEMPLATE = os.path.join(FRAMEWORK_ROOT, "data_dictionary_template.md")

ALL_NODES = ["eda", "segmentation", "profiling", "driver_analysis", "insight_synthesis"]

NODE_TEMPLATES = {
    "eda": {
        "status": "pending",
        "started": "",
        "completed": "",
        "findings": {},
        "user_decisions": {},
        "flags_raised": [],
        "flags_resolved": []
    },
    "segmentation": {
        "status": "pending",
        "started": "",
        "completed": "",
        "findings": {},
        "user_decisions": {},
        "iterations": [],
        "approved_segmentation": {}
    },
    "profiling": {
        "status": "pending",
        "started": "",
        "completed": "",
        "findings": {},
        "user_decisions": {},
        "key_differentiators": []
    },
    "driver_analysis": {
        "status": "pending",
        "started": "",
        "completed": "",
        "findings": {},
        "user_decisions": {},
        "top_drivers": [],
        "flags_for_validation": []
    },
    "insight_synthesis": {
        "status": "pending",
        "started": "",
        "completed": "",
        "narrative": "",
        "recommendations": [],
        "user_decisions": {}
    }
}

def prompt(label, required=True):
    while True:
        value = input(f"  {label}: ").strip()
        if value or not required:
            return value
        print("    This field is required.")

def prompt_yn(label):
    while True:
        value = input(f"  {label} (y/n): ").strip().lower()
        if value in ("y", "n"):
            return value == "y"
        print("    Please enter y or n.")

def collect_skipped_nodes():
    skipped = {}
    print("\n  Which nodes do you want to skip? (press Enter to keep all nodes)")
    print("  Available nodes:", ", ".join(ALL_NODES))
    raw = input("  Nodes to skip (comma-separated, or leave blank): ").strip()
    if not raw:
        return skipped
    names = [n.strip() for n in raw.split(",")]
    for name in names:
        if name not in ALL_NODES:
            print(f"    Warning: '{name}' is not a recognised node — skipping this entry.")
            continue
        reason = input(f"  Reason for skipping '{name}': ").strip()
        skipped[name] = reason or "No reason given"
    return skipped

def build_state(analysis_id, business_question, csv_filename, skipped_nodes):
    nodes = {}
    nodes_to_run = []
    nodes_to_skip = list(skipped_nodes.keys())

    for node in ALL_NODES:
        if node in skipped_nodes:
            nodes[node] = {
                "status": "skipped",
                "reason": skipped_nodes[node]
            }
        else:
            nodes[node] = NODE_TEMPLATES[node].copy()
            nodes_to_run.append(node)

    return {
        "session": {
            "started": "",
            "last_updated": "",
            "analysis_id": analysis_id,
            "status": "not_started"
        },
        "intake": {
            "business_question": business_question,
            "dataset": f"data/{csv_filename}",
            "data_dictionary": "data/data_dictionary.md",
            "population": "",
            "time_period": "",
            "hypotheses": [],
            "nodes_to_run": nodes_to_run,
            "nodes_to_skip": nodes_to_skip
        },
        "decisions": [],
        "notes": [],
        "columns_excluded": [],
        "columns_retained": [],
        "null_treatments": {},
        "segment_definitions": {},
        "nodes": nodes
    }

def main():
    print("\n" + "="*60)
    print("  Automated Insights Platform — New Analysis Setup")
    print("="*60)

    print("\n--- Step 1: Analysis Identity ---")
    print("  Use snake_case, e.g. credit_card_segmentation, churn_q1_2025")
    analysis_id = prompt("Analysis ID (snake_case)")
    if not analysis_id.replace("_", "").isalnum():
        print("  Warning: analysis_id should contain only letters, numbers, and underscores.")

    analysis_dir = os.path.join(ANALYSES_DIR, analysis_id)
    if os.path.exists(analysis_dir):
        print(f"\n  A folder already exists at analyses/{analysis_id}.")
        overwrite = prompt_yn("  Overwrite it")
        if not overwrite:
            print("  Exiting — no changes made.")
            return

    print("\n--- Step 2: Business Question ---")
    print("  State the core question this analysis must answer.")
    business_question = prompt("Business question")

    print("\n--- Step 3: Dataset ---")
    print("  Just the filename, e.g. cc_general.csv — not the full path.")
    csv_filename = prompt("CSV filename")

    print("\n--- Step 4: Nodes ---")
    skipped_nodes = collect_skipped_nodes()

    # Create folder structure
    print("\n--- Creating folder structure ---")
    folders = [
        analysis_dir,
        os.path.join(analysis_dir, "data"),
        os.path.join(analysis_dir, "outputs", "eda_charts")
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  Created: {os.path.relpath(folder, FRAMEWORK_ROOT)}/")

    # Copy intake template
    intake_dest = os.path.join(analysis_dir, "intake.md")
    shutil.copy(INTAKE_TEMPLATE, intake_dest)
    print(f"  Copied:  analyses/{analysis_id}/intake.md  ← fill this in before running EDA")

    # Copy data dictionary template
    dict_dest = os.path.join(analysis_dir, "data", "data_dictionary.md")
    shutil.copy(DATA_DICT_TEMPLATE, dict_dest)
    print(f"  Copied:  analyses/{analysis_id}/data/data_dictionary.md  ← fill this in before running EDA")

    # Write state.json
    state = build_state(analysis_id, business_question, csv_filename, skipped_nodes)
    state_path = os.path.join(analysis_dir, "state.json")
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"  Created: analyses/{analysis_id}/state.json")

    # Summary
    print("\n" + "="*60)
    print(f"  Analysis '{analysis_id}' is ready.")
    print("="*60)
    print("\n  Next steps:")
    print(f"  1. Place your CSV at:  analyses/{analysis_id}/data/{csv_filename}")
    print(f"  2. Fill in:            analyses/{analysis_id}/intake.md")
    print(f"  3. Fill in:            analyses/{analysis_id}/data/data_dictionary.md")
    print(f"  4. Open Claude Code and say:")
    print(f'     "I am starting a new analysis called {analysis_id}.')
    print(f'      Please read the intake file, data dictionary, and EDA skill, then run EDA."')
    print()

    if skipped_nodes:
        print(f"  Nodes skipped: {', '.join(skipped_nodes.keys())}")
        print(f"  Nodes to run:  {', '.join([n for n in ALL_NODES if n not in skipped_nodes])}")

    print()

if __name__ == "__main__":
    main()
