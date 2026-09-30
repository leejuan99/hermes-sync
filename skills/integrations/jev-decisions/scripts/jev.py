#!/usr/bin/env python3
"""Jev (TypeSafe) decision helper for Hermes.

Jev is a *decision* model, not a chat model. It takes a `state` (the facts)
plus `questions` (typed primitives) and returns typed answers with
probabilities -- no prose.

Usage:
  python jev.py --state '{"message":"..."}' --questions questions.json
  python jev.py --state-file state.json --questions-file q.json --pretty

Primitives (question types):
  noul   -> P(yes), 0..1
  choice -> winning key + per-option probabilities + confidence
  score  -> weighted position on ordered criteria + per-level probabilities

Reads the key from $OPENROUTER_API_KEY (never hardcode it).
Endpoint: POST https://openrouter.ai/api/alpha/decisions
Model:    typesafe/jev-1.13   (alias: ~typesafe/jev-latest)
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"


def decide(state, questions, model=DEFAULT_MODEL, session_id=None, timeout=60):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY not set in environment")

    payload = {"model": model, "state": state, "questions": questions}
    if session_id:
        payload["session_id"] = session_id

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise SystemExit(f"HTTP {e.code}: {body}")


def _load(inline, path):
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if inline:
        return json.loads(inline)
    return None


def main():
    p = argparse.ArgumentParser(description="Call TypeSafe Jev via OpenRouter")
    p.add_argument("--state", help="JSON string of the state/facts")
    p.add_argument("--state-file", help="Path to a JSON file with the state")
    p.add_argument("--questions", help="JSON string of questions")
    p.add_argument("--questions-file", help="Path to a JSON file with questions")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--session-id", default=None)
    p.add_argument("--pretty", action="store_true", help="Indent output")
    p.add_argument("--answers-only", action="store_true",
                   help="Print only the answers object")
    args = p.parse_args()

    state = _load(args.state, args.state_file)
    questions = _load(args.questions, args.questions_file)
    if state is None or questions is None:
        p.error("need --state/--state-file and --questions/--questions-file")

    out = decide(state, questions, model=args.model, session_id=args.session_id)
    if args.answers_only and "answers" in out:
        out = out["answers"]
    print(json.dumps(out, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
