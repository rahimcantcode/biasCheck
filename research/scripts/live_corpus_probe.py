"""Sequential reproducible live API baseline, preserving every raw response."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import requests


def run(data, output):
    rows = [json.loads(s) for s in data.read_text().splitlines()]
    if output.exists():
        raise ValueError("Refusing to overwrite a run")
    session = requests.Session()
    response = session.get("https://bias.r4him.tech/api/health", timeout=30)
    response.raise_for_status()
    health = response.json()
    record = {"started_at": time.time(), "input_sha256": hashlib.sha256(data.read_bytes()).hexdigest(), "health": health, "results": []}
    output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    for row in rows:
        started = time.monotonic()
        item = {"id": row["id"]}
        try:
            response = session.post("https://bias.r4him.tech/api/predict", json={"input": row["text"], "mode": "article"}, timeout=120)
            response.raise_for_status()
            item["response"] = response.json()
            failures = 0
        except Exception as exc:
            item["error"] = str(exc)
            failures += 1
        item["seconds"] = time.monotonic() - started
        record["results"].append(item)
        output.write_text(json.dumps(record, indent=2))
        print(len(record["results"]), "/", len(rows), item.get("error") or item["response"]["overall"]["raw_label"], flush=True)
        if failures >= 3:
            raise RuntimeError("Three consecutive failures; stopping probe")
    record["finished_at"] = time.time()
    output.write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.input, args.output)
