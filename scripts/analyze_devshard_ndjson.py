#!/usr/bin/env python3
"""Stream-analyze large devshard NDJSON exports for P3-CAND-01."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


CASE_ADDRESSES = {
    "gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4",
    "gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau",
    "gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw",
    "gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv",
    "gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5",
    "gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n",
    "gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s",
}


def iter_jsonl(path: Path):
    with path.open(errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="artifacts")
    parser.add_argument("--epoch", type=int, default=272)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    epoch = args.epoch

    inferences_path = data_dir / "devshard_inferences.ndjson"
    validations_path = data_dir / "devshard_validations.ndjson"
    diffs_path = data_dir / "devshard_diffs.ndjson"
    settlements_path = data_dir / "devshard_settlements.ndjson"

    escrow_epochs: dict[int, int] = {}
    escrow_inference_count = Counter()
    executor_stats = defaultdict(Counter)
    status_counts = Counter()
    model_counts = Counter()
    input_lengths = []
    case_executor_rows = []

    for row in iter_jsonl(inferences_path):
        escrow_id = int(row["escrow_id"])
        row_epoch = int(row.get("epoch_index") or 0)
        escrow_epochs[escrow_id] = row_epoch
        if row_epoch != epoch:
            continue
        escrow_inference_count[escrow_id] += 1
        status_counts[row.get("status") or ""] += 1
        model_counts[row.get("model") or ""] += 1
        input_lengths.append(int(row.get("input_length_claimed") or 0))
        executor = row.get("executor_address") or ""
        stats = executor_stats[executor]
        stats["executed"] += 1
        stats["cost"] += int(row.get("cost") or 0)
        stats["output_tokens"] += int(row.get("output_tokens") or 0)
        stats["input_tokens_actual"] += int(row.get("input_tokens_actual") or 0)
        if executor in CASE_ADDRESSES:
            case_executor_rows.append(row)

    validation_stats = defaultdict(Counter)
    validation_by_escrow = defaultdict(Counter)
    case_validation_rows = []
    total_validation_rows_epoch = 0
    for row in iter_jsonl(validations_path):
        escrow_id = int(row["escrow_id"])
        if escrow_epochs.get(escrow_id) != epoch:
            continue
        total_validation_rows_epoch += 1
        validator = row.get("validator_addr") or ""
        stats = validation_stats[validator]
        stats["validation_rows"] += 1
        if int(row.get("valid") or 0):
            stats["valid_true"] += 1
            validation_by_escrow[escrow_id]["valid_true"] += 1
        else:
            stats["valid_false"] += 1
            validation_by_escrow[escrow_id]["valid_false"] += 1
        if int(row.get("is_vote") or 0):
            stats["is_vote_true"] += 1
        else:
            stats["is_vote_false"] += 1
        if validator in CASE_ADDRESSES:
            case_validation_rows.append(row)

    diff_counts = Counter()
    diff_tx_kind_counts = Counter()
    for row in iter_jsonl(diffs_path):
        escrow_id = int(row["escrow_id"])
        if escrow_epochs.get(escrow_id) != epoch:
            continue
        diff_counts["rows"] += 1
        diff_counts["tx_count"] += int(row.get("tx_count") or 0)
        for kind in row.get("tx_kinds") or []:
            diff_tx_kind_counts[kind] += 1

    settlement_rows = []
    for row in iter_jsonl(settlements_path):
        escrow_id = int(row["escrow_id"])
        if escrow_epochs.get(escrow_id) == epoch:
            settlement_rows.append(row)

    participant_rows = []
    addresses = sorted(set(executor_stats) | set(validation_stats) | CASE_ADDRESSES)
    for addr in addresses:
        executed = executor_stats[addr]
        validated = validation_stats[addr]
        participant_rows.append(
            {
                "participant": addr,
                "case_address": addr in CASE_ADDRESSES,
                "executed": executed["executed"],
                "execution_cost": executed["cost"],
                "validation_rows": validated["validation_rows"],
                "valid_true": validated["valid_true"],
                "valid_false": validated["valid_false"],
                "is_vote_true": validated["is_vote_true"],
                "is_vote_false": validated["is_vote_false"],
            }
        )

    write_csv(
        out_dir / f"devshard_epoch_{epoch}_participant_activity.csv",
        participant_rows,
        [
            "participant",
            "case_address",
            "executed",
            "execution_cost",
            "validation_rows",
            "valid_true",
            "valid_false",
            "is_vote_true",
            "is_vote_false",
        ],
    )
    write_csv(
        out_dir / f"devshard_epoch_{epoch}_case_executor_rows.csv",
        case_executor_rows,
        sorted(case_executor_rows[0].keys()) if case_executor_rows else ["escrow_id"],
    )
    write_csv(
        out_dir / f"devshard_epoch_{epoch}_case_validation_rows.csv",
        case_validation_rows,
        sorted(case_validation_rows[0].keys()) if case_validation_rows else ["escrow_id"],
    )

    summary = {
        "epoch": epoch,
        "escrow_count_from_inferences": len(escrow_inference_count),
        "inference_count": sum(escrow_inference_count.values()),
        "validation_rows": total_validation_rows_epoch,
        "diff_rows": diff_counts["rows"],
        "diff_tx_count": diff_counts["tx_count"],
        "settlement_event_count": len(settlement_rows),
        "status_counts": dict(status_counts),
        "model_counts": dict(model_counts),
        "diff_tx_kind_counts": dict(diff_tx_kind_counts),
        "input_length_claimed": {
            "count": len(input_lengths),
            "min": min(input_lengths) if input_lengths else 0,
            "max": max(input_lengths) if input_lengths else 0,
            "avg": sum(input_lengths) / len(input_lengths) if input_lengths else 0,
        },
        "case_addresses": sorted(CASE_ADDRESSES),
        "case_executor_row_count": len(case_executor_rows),
        "case_validation_row_count": len(case_validation_rows),
        "case_participant_activity": [
            row for row in participant_rows if row["case_address"]
        ],
    }
    (out_dir / f"devshard_epoch_{epoch}_ndjson_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
