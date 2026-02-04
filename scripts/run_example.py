#!/usr/bin/env python3
"""Simple example runner to demonstrate the Publication Assistant pipeline on a temporary repo.

This script creates a tiny repository in a temp directory, builds the agents,
runs the orchestrator pipeline, and prints a short summary. It's intentionally
lightweight and does not require external LLM keys to run the heuristics.
"""
import tempfile
import os
import shutil
from main import build_agents
from orchestration import Orchestrator
from utils.logging import configure_logging

configure_logging()


def create_sample_repo(path: str):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
        f.write(
            "Sample Project\n\nThis project demonstrates a small example. Usage: python run.py\n\nInstallation: pip install -r requirements.txt"
        )
    with open(os.path.join(path, "run.py"), "w", encoding="utf-8") as f:
        f.write("print('hello world')\n")


def main():
    tmp = tempfile.mkdtemp(prefix="pubassist_")
    try:
        create_sample_repo(tmp)
        agents, bus = build_agents(tmp)
        orchestrator = Orchestrator(bus)
        result = orchestrator.run_pipeline(agents, tmp)

        print("=== Example Run Result Summary ===")
        analysis = result.get("analysis")
        metadata = result.get("metadata")
        review = result.get("review")

        if analysis:
            missing = getattr(analysis, "missing_sections", None)
            print("Missing README sections:", missing)
        else:
            print("No analysis returned.")

        if metadata:
            titles = getattr(metadata, "title_suggestions", None)
            tags = getattr(metadata, "tags", None)
            print("Title suggestions:", titles)
            print("Tags:", tags)
        else:
            print("No metadata returned.")

        if review:
            score = getattr(review, "score", None)
            print("Review score:", score)
        else:
            print("No review returned.")

    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
