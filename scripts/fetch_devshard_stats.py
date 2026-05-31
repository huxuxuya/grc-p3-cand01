#!/usr/bin/env python3
"""Fetch devshard host epoch stats for case participants.

The endpoint is useful only while devshard host stats are retained on-chain.
For old epochs it should return found=false; the script records that result so
the evidence gap is explicit and reproducible.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "http://node1.gonka.ai:8000"
DEVSHARD_PRUNING_THRESHOLD = 2


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def read_targets(path: Path) -> list[tuple[int, str]]:
    targets: set[tuple[int, str]] = set()
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            epoch = int(row["epoch"])
            participant = row["participant_id"]
            targets.add((epoch, participant))
    return sorted(targets)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "epoch",
        "participant_id",
        "found",
        "likely_pruned",
        "current_epoch",
        "retention_threshold_epochs",
        "missed",
        "invalid",
        "cost",
        "required_validations",
        "completed_validations",
        "escrow_count",
        "raw_file",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--targets-csv", default="artifacts/zero_reward_269_272.csv")
    parser.add_argument("--raw-dir", default="data/raw/devshard")
    parser.add_argument("--out-dir", default="artifacts")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    targets = read_targets(Path(args.targets_csv))

    current_epoch_url = (
        f"{base}/chain-api/productscience/inference/inference/get_current_epoch"
    )
    print(f"fetch {current_epoch_url}", file=sys.stderr)
    current_epoch_payload = fetch_json(current_epoch_url)
    current_epoch = int(current_epoch_payload["epoch"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "current_epoch.json").write_text(
        json.dumps(current_epoch_payload, indent=2, sort_keys=True) + "\n"
    )

    rows = []
    for epoch, participant in targets:
        endpoint = (
            f"/chain-api/productscience/inference/inference/"
            f"devshard_host_epoch_stats/{epoch}/{participant}"
        )
        url = f"{base}{endpoint}"
        print(f"fetch {url}", file=sys.stderr)
        payload = fetch_json(url)
        raw_file = (
            raw_dir
            / f"devshard_host_epoch_stats_{epoch}_{safe_name(participant)}.json"
        )
        raw_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

        stats = payload.get("stats") or {}
        found = bool(payload.get("found"))
        likely_pruned = epoch <= current_epoch - DEVSHARD_PRUNING_THRESHOLD
        rows.append(
            {
                "epoch": epoch,
                "participant_id": participant,
                "found": found,
                "likely_pruned": likely_pruned,
                "current_epoch": current_epoch,
                "retention_threshold_epochs": DEVSHARD_PRUNING_THRESHOLD,
                "missed": stats.get("missed", ""),
                "invalid": stats.get("invalid", ""),
                "cost": stats.get("cost", ""),
                "required_validations": stats.get("required_validations", ""),
                "completed_validations": stats.get("completed_validations", ""),
                "escrow_count": stats.get("escrow_count", ""),
                "raw_file": str(raw_file),
            }
        )

    write_csv(out_dir / "devshard_host_stats_audit.csv", rows)
    summary = {
        "current_epoch": current_epoch,
        "retention_threshold_epochs": DEVSHARD_PRUNING_THRESHOLD,
        "target_count": len(rows),
        "found_count": sum(1 for row in rows if row["found"]),
        "not_found_count": sum(1 for row in rows if not row["found"]),
        "likely_pruned_count": sum(1 for row in rows if row["likely_pruned"]),
        "targets_csv": args.targets_csv,
        "notes": [
            "found=false means no retained on-chain devshard host stats for that epoch/participant at query time",
            "epochs older than current_epoch - 2 are expected to be pruned by the devshard pruner",
        ],
    }
    (out_dir / "devshard_host_stats_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
