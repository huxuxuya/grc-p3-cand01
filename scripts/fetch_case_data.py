#!/usr/bin/env python3
"""Fetch raw chain data for P3-CAND-01.

The script writes only raw API responses. Analysis is handled by
scripts/analyze_case.py so reviewers can inspect source data separately.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "http://node1.gonka.ai:8000"
DEFAULT_EPOCHS = (269, 270, 271, 272)


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--out-dir", default="data/raw")
    parser.add_argument("--epochs", nargs="*", type=int, default=DEFAULT_EPOCHS)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    base = args.base_url.rstrip("/")

    endpoints = {
        "params": "/chain-api/productscience/inference/inference/params",
    }

    for name, endpoint in endpoints.items():
        url = f"{base}{endpoint}"
        print(f"fetch {url}", file=sys.stderr)
        write_json(out_dir / f"{name}.json", fetch_json(url))

    for epoch in args.epochs:
        epoch_endpoints = {
            f"epoch_{epoch}_performance_summary": (
                f"/chain-api/productscience/inference/inference/"
                f"epoch_performance_summary/{epoch}"
            ),
            f"epoch_{epoch}_group_data": (
                f"/chain-api/productscience/inference/inference/"
                f"epoch_group_data/{epoch}"
            ),
        }
        for name, endpoint in epoch_endpoints.items():
            url = f"{base}{endpoint}"
            print(f"fetch {url}", file=sys.stderr)
            try:
                write_json(out_dir / f"{name}.json", fetch_json(url))
            except urllib.error.URLError as exc:
                print(f"error fetching {url}: {exc}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
