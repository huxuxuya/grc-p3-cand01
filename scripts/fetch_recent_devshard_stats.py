#!/usr/bin/env python3
"""Fetch devshard host stats for the current and previous epochs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "http://node1.gonka.ai:8000"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def participants_from_performance(payload: dict) -> set[str]:
    return {
        row["participant_id"]
        for row in payload.get("epochPerformanceSummary", [])
        if row.get("participant_id")
    }


def participants_from_group_data(payload: dict) -> set[str]:
    group = payload.get("epoch_group_data") or {}
    addresses = {
        row["member_address"]
        for row in group.get("validation_weights", [])
        if row.get("member_address")
    }
    addresses.update(
        row["member_address"]
        for row in group.get("member_seed_signatures", [])
        if row.get("member_address")
    )
    return addresses


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "epoch",
        "participant",
        "source",
        "found",
        "missed",
        "invalid",
        "cost",
        "required_validations",
        "completed_validations",
        "escrow_count",
        "raw_file",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--out-dir", default="data/raw/devshard_recent")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument(
        "--epochs",
        nargs="*",
        type=int,
        help="Epochs to fetch. Defaults to current-1 and current.",
    )
    parser.add_argument("--sleep", type=float, default=0.05)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    out_dir = Path(args.out_dir)
    artifacts_dir = Path(args.artifacts_dir)

    current_payload = fetch_json(
        f"{base}/chain-api/productscience/inference/inference/get_current_epoch"
    )
    current_epoch = int(current_payload["epoch"])
    epochs = args.epochs or [current_epoch - 1, current_epoch]
    write_json(out_dir / "current_epoch.json", current_payload)

    all_rows: list[dict] = []
    summary: list[dict] = []

    for epoch in epochs:
        perf_url = (
            f"{base}/chain-api/productscience/inference/inference/"
            f"epoch_performance_summary/{epoch}"
        )
        group_url = (
            f"{base}/chain-api/productscience/inference/inference/"
            f"epoch_group_data/{epoch}"
        )
        print(f"fetch {perf_url}", file=sys.stderr)
        perf_payload = fetch_json(perf_url)
        write_json(out_dir / f"epoch_{epoch}_performance_summary.json", perf_payload)

        participants = participants_from_performance(perf_payload)
        source = "performance_summary"
        if not participants:
            print(f"fetch {group_url}", file=sys.stderr)
            group_payload = fetch_json(group_url)
            write_json(out_dir / f"epoch_{epoch}_group_data.json", group_payload)
            participants = participants_from_group_data(group_payload)
            source = "epoch_group_data"

        found_count = 0
        sums = {
            "missed": 0,
            "invalid": 0,
            "cost": 0,
            "required_validations": 0,
            "completed_validations": 0,
            "escrow_count": 0,
        }
        for participant in sorted(participants):
            url = (
                f"{base}/chain-api/productscience/inference/inference/"
                f"devshard_host_epoch_stats/{epoch}/{participant}"
            )
            payload = fetch_json(url)
            raw_file = (
                out_dir
                / f"epoch_{epoch}"
                / f"devshard_host_epoch_stats_{safe_name(participant)}.json"
            )
            write_json(raw_file, payload)
            stats = payload.get("stats") or {}
            found = bool(payload.get("found"))
            if found:
                found_count += 1
            row = {
                "epoch": epoch,
                "participant": participant,
                "source": source,
                "found": found,
                "raw_file": str(raw_file),
            }
            for key in sums:
                value = int(stats.get(key) or 0)
                row[key] = value if found else ""
                if found:
                    sums[key] += value
            all_rows.append(row)
            time.sleep(args.sleep)

        summary.append(
            {
                "epoch": epoch,
                "participant_source": source,
                "participant_count": len(participants),
                "devshard_found_count": found_count,
                "devshard_not_found_count": len(participants) - found_count,
                **{f"devshard_{key}_sum": value for key, value in sums.items()},
            }
        )

    write_csv(artifacts_dir / "recent_devshard_host_stats.csv", all_rows)
    write_json(
        artifacts_dir / "recent_devshard_host_stats_summary.json",
        {
            "current_epoch": current_epoch,
            "epochs": epochs,
            "summary": summary,
        },
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
