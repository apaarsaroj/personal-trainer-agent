"""Measure the Trainer Agent so resume numbers are real.

Run from the project root:
    uv run python scripts/measure_agent.py

Part 1 (free, offline): does retrieval return relevant text for known questions?
Part 2 (uses your Anthropic API key, a few cents): how long does the agent take to answer?
Neither part writes to your workout or user data.
"""

import json
import os
import statistics
import sys
import time

# Make the project root importable and the working directory, wherever this is launched from.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from langgraph.checkpoint.memory import MemorySaver

from trainer.knowledge_base import retrieve

# (question, words that should appear somewhere in the top 3 retrieved chunks).
# Edit these so they match what YOUR knowledge base should know. A question counts as a
# hit if ANY of its words appears in the top 3 chunks.
RETRIEVAL_CHECKS = [
    ("What muscles does the barbell squat work?", ["quadriceps", "glutes", "squat"]),
    ("How do I perform a deadlift with good form?", ["deadlift", "hip", "hamstring"]),
    ("What is progressive overload?", ["progressive", "overload"]),
    ("How much protein do I need to build muscle?", ["protein"]),
    ("How many rest days should I take?", ["rest", "recovery"]),
    ("What exercises train the chest?", ["pectoralis", "chest", "bench"]),
    ("How do I strengthen my back?", ["latissimus", "back", "row"]),
    ("What are good exercises for shoulders?", ["deltoid", "shoulder", "press"]),
    ("How does sleep affect muscle recovery?", ["sleep"]),
    ("What is a good rep range for hypertrophy?", ["hypertrophy", "reps", "repetitions"]),
]

LATENCY_QUESTIONS = [
    "What muscles does the barbell squat work?",
    "How much protein should I eat to build muscle?",
    "How many rest days should I take per week?",
    "What is progressive overload?",
    "Explain proper deadlift form.",
]


def check_retrieval():
    hits = 0
    for question, words in RETRIEVAL_CHECKS:
        chunks = retrieve(question, n_results=3)
        text = " ".join(chunks).lower()
        hit = any(w.lower() in text for w in words)
        hits += hit
        print(f"  {'HIT ' if hit else 'MISS'}  {question}")
    print(
        f"\nRetrieval: {hits} of {len(RETRIEVAL_CHECKS)} questions returned relevant text in the top 3 chunks"
    )


def check_latency():
    from trainer.graph import create_graph, run_graph

    with open("data/users.json") as f:
        profile = next(iter(json.load(f).values()))

    graph = create_graph(profile, MemorySaver())
    times = []
    for i, question in enumerate(LATENCY_QUESTIONS):
        start = time.perf_counter()
        run_graph(question, profile, graph, thread_id=f"measure-{i}")
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  {elapsed:5.1f}s  {question}")
    print(
        f"\nLatency over {len(times)} questions: mean {statistics.mean(times):.1f}s, "
        f"median {statistics.median(times):.1f}s, slowest {max(times):.1f}s"
    )


if __name__ == "__main__":
    print("Part 1: retrieval check\n")
    check_retrieval()
    print("\nPart 2: response time (calls the Anthropic API)\n")
    check_latency()
