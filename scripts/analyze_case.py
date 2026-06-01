#!/usr/bin/env python3
"""Analyze P3-CAND-01 raw data and write reproducible artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 50

REPORTED_ADDRESSES = {
    "gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4",
    "gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau",
    "gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw",
    "gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv",
    "gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5",
    "gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def dec_from_param(value: dict) -> Decimal:
    return Decimal(int(value["value"])) * (Decimal(10) ** int(value["exponent"]))


def fixed_epoch_reward(params: dict, epoch: int) -> int:
    reward_params = params["params"]["bitcoin_reward_params"]
    initial = Decimal(int(reward_params["initial_epoch_reward"]))
    decay = dec_from_param(reward_params["decay_rate"])
    genesis = int(reward_params["genesis_epoch"])
    epochs_since_genesis = epoch - genesis
    if epochs_since_genesis <= 0:
        return int(initial)
    return int(initial * (decay.exp() ** epochs_since_genesis))


def calculate_power_capped_weights(weights: dict[str, int]) -> tuple[dict[str, int], bool]:
    """Match chain ApplyPowerCappingForWeights for settlement effective weights."""
    if len(weights) <= 1:
        return dict(weights), False

    participant_count = len(weights)
    max_percentage = Decimal("0.30")
    if participant_count == 2:
        max_percentage = Decimal("0.50")
    elif participant_count == 3:
        max_percentage = Decimal("0.40")

    sorted_weights = sorted(weights.items(), key=lambda item: item[1])
    cap = None
    sum_previous = 0
    for index, (_, current_weight) in enumerate(sorted_weights):
        remaining = participant_count - index
        weighted_total = sum_previous + current_weight * remaining
        threshold = max_percentage * Decimal(weighted_total)
        if Decimal(current_weight) > threshold:
            numerator = max_percentage * Decimal(sum_previous)
            denominator = Decimal(1) - max_percentage * Decimal(remaining)
            if denominator <= 0:
                cap = current_weight
            else:
                cap = int(numerator / denominator)
            break
        sum_previous += current_weight

    if cap is None:
        return dict(weights), False

    return {participant: min(weight, cap) for participant, weight in weights.items()}, True


def model_group_path(raw_dir: Path, epoch: int, model_id: str) -> Path:
    encoded = urllib.parse.quote(model_id, safe="")
    return raw_dir / f"epoch_{epoch}_group_data_model_{encoded}.json"


def model_coefficients(params: dict) -> dict[str, Decimal]:
    models = params["params"].get("poc_params", {}).get("models", [])
    return {
        model["model_id"]: dec_from_param(model["weight_scale_factor"])
        for model in models
        if model.get("model_id") and model.get("weight_scale_factor")
    }


def load_model_subgroups(raw_dir: Path, epoch: int, parent_group: dict) -> dict[str, dict]:
    subgroups = {}
    for model_id in parent_group.get("sub_group_models", []):
        path = model_group_path(raw_dir, epoch, model_id)
        if not path.exists():
            raise FileNotFoundError(
                f"missing model subgroup data for epoch {epoch}, model {model_id}: {path}. "
                "Run scripts/fetch_case_data.py to fetch chain subgroup epoch_group_data."
            )
        payload = read_json(path)
        group = payload["epoch_group_data"]
        if group.get("model_id") != model_id:
            raise ValueError(
                f"model subgroup file {path} contains model_id={group.get('model_id')!r}, "
                f"expected {model_id!r}"
            )
        subgroups[model_id] = group
    return subgroups


def calculate_raw_totals(
    parent_group: dict, subgroups: dict[str, dict], coefficients: dict[str, Decimal]
) -> dict[str, int]:
    raw_totals = {
        row["member_address"]: 0
        for row in parent_group.get("validation_weights", [])
    }
    for model_id, group in subgroups.items():
        coefficient = coefficients.get(model_id, Decimal(1))
        for row in group.get("validation_weights", []):
            raw_model = sum(
                int(node.get("poc_weight", 0))
                for node in row.get("ml_nodes", [])
                if node is not None
            )
            raw_totals[row["member_address"]] = (
                raw_totals.get(row["member_address"], 0)
                + int(coefficient * Decimal(raw_model))
            )
    return raw_totals


def load_weights(
    raw_dir: Path, params: dict, epoch: int
) -> tuple[dict[str, dict[str, int]], int, bool]:
    payload = read_json(raw_dir / f"epoch_{epoch}_group_data.json")
    group = payload["epoch_group_data"]
    subgroups = load_model_subgroups(raw_dir, epoch, group)
    raw_totals = calculate_raw_totals(group, subgroups, model_coefficients(params))

    rows = {}
    uncapped_effective_weights = {}
    full_weight_sum = 0
    for row in group.get("validation_weights", []):
        addr = row["member_address"]
        full_weight = max(int(row["weight"]), 0)
        confirmation_weight = max(int(row.get("confirmation_weight", 0)), 0)
        raw_total = raw_totals.get(addr, 0)
        effective_weight = confirmation_weight
        if raw_total > 0 and full_weight < raw_total:
            effective_weight = (confirmation_weight * full_weight) // raw_total
        if effective_weight > full_weight:
            effective_weight = full_weight

        rows[addr] = {
            "full_weight": full_weight,
            "confirmation_weight": confirmation_weight,
            "raw_total": raw_total,
            "chain_effective_weight_uncapped": effective_weight,
            "chain_effective_weight": effective_weight,
        }
        uncapped_effective_weights[addr] = effective_weight
        full_weight_sum += full_weight

    effective_weights, was_power_capped = calculate_power_capped_weights(
        uncapped_effective_weights
    )
    for addr, effective_weight in effective_weights.items():
        rows[addr]["chain_effective_weight"] = effective_weight

    total_weight = int(group.get("total_weight") or full_weight_sum)
    if total_weight != full_weight_sum:
        raise ValueError(
            f"epoch {epoch} total_weight={total_weight} differs from parent full weight sum={full_weight_sum}"
        )
    return rows, total_weight, was_power_capped


def analyze_epoch(raw_dir: Path, params: dict, epoch: int) -> tuple[dict, list[dict]]:
    summary = read_json(raw_dir / f"epoch_{epoch}_performance_summary.json")
    weights, total_weight, was_power_capped = load_weights(raw_dir, params, epoch)
    fixed_reward = fixed_epoch_reward(params, epoch)
    rows = []

    for item in summary.get("epochPerformanceSummary", []):
        addr = item["participant_id"]
        inference_count = int(item["inference_count"])
        missed_requests = int(item["missed_requests"])
        earned_coins = int(item["earned_coins"])
        rewarded_coins = int(item["rewarded_coins"])
        total_requests = inference_count + missed_requests
        miss_rate = None
        if total_requests:
            miss_rate = missed_requests / total_requests
        weight = weights.get(
            addr,
            {
                "full_weight": 0,
                "confirmation_weight": 0,
                "raw_total": 0,
                "chain_effective_weight_uncapped": 0,
                "chain_effective_weight": 0,
            },
        )
        full_weight = weight["full_weight"]
        confirmation_weight = weight["confirmation_weight"]
        raw_total = weight["raw_total"]
        uncapped_effective_weight = weight["chain_effective_weight_uncapped"]
        effective_weight = weight["chain_effective_weight"]
        expected_reward = 0
        if total_weight > 0 and effective_weight > 0:
            expected_reward = (effective_weight * fixed_reward) // total_weight
        preliminary_exposure = max(expected_reward - rewarded_coins, 0)
        zero_reward = rewarded_coins == 0
        claimed = bool(item["claimed"])

        rows.append(
            {
                "epoch": epoch,
                "participant_id": addr,
                "reported_address": addr in REPORTED_ADDRESSES,
                "claimed": claimed,
                "inference_count": inference_count,
                "missed_requests": missed_requests,
                "miss_rate": miss_rate,
                "earned_coins": earned_coins,
                "rewarded_coins": rewarded_coins,
                "validation_weight": full_weight,
                "full_weight": full_weight,
                "confirmation_weight": confirmation_weight,
                "raw_total": raw_total,
                "chain_effective_weight_uncapped": uncapped_effective_weight,
                "chain_effective_weight": effective_weight,
                "total_epoch_weight": total_weight,
                "fixed_epoch_reward": fixed_reward,
                "expected_reward_pre_downtime": expected_reward,
                "preliminary_exposure": preliminary_exposure,
                "zero_reward": zero_reward,
                "zero_reward_claimed": zero_reward and claimed,
                "needs_root_cause_review": zero_reward and (
                    addr in REPORTED_ADDRESSES or claimed or earned_coins > 0
                ),
            }
        )

    aggregate = {
        "epoch": epoch,
        "participant_count": len(rows),
        "zero_reward_count": sum(1 for row in rows if row["zero_reward"]),
        "zero_reward_claimed_count": sum(
            1 for row in rows if row["zero_reward_claimed"]
        ),
        "reported_address_count": sum(1 for row in rows if row["reported_address"]),
        "reported_zero_reward_count": sum(
            1 for row in rows if row["reported_address"] and row["zero_reward"]
        ),
        "total_inference_count": sum(row["inference_count"] for row in rows),
        "total_missed_requests": sum(row["missed_requests"] for row in rows),
        "total_earned_coins": sum(row["earned_coins"] for row in rows),
        "total_rewarded_coins": sum(row["rewarded_coins"] for row in rows),
        "fixed_epoch_reward": fixed_reward,
        "total_epoch_weight": total_weight,
        "power_capping_applied": was_power_capped,
        "reported_preliminary_exposure": sum(
            row["preliminary_exposure"] for row in rows if row["reported_address"]
        ),
        "claimed_zero_reward_preliminary_exposure": sum(
            row["preliminary_exposure"] for row in rows if row["zero_reward_claimed"]
        ),
    }
    return aggregate, rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = row.copy()
            if "miss_rate" in fieldnames and isinstance(csv_row.get("miss_rate"), float):
                csv_row["miss_rate"] = f"{csv_row['miss_rate']:.8f}"
            elif "miss_rate" in fieldnames and csv_row.get("miss_rate") is None:
                csv_row["miss_rate"] = ""
            csv_row = {field: csv_row.get(field, "") for field in fieldnames}
            writer.writerow(csv_row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--out-dir", default="artifacts")
    parser.add_argument("--epochs", nargs="*", type=int, default=[269, 270, 271, 272])
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    params = read_json(raw_dir / "params.json")

    all_rows = []
    aggregates = []
    for epoch in args.epochs:
        aggregate, rows = analyze_epoch(raw_dir, params, epoch)
        aggregates.append(aggregate)
        all_rows.extend(rows)

    interesting_rows = [
        row
        for row in all_rows
        if row["epoch"] == 272
        and (row["reported_address"] or row["zero_reward_claimed"])
    ]
    zero_reward_rows = [row for row in all_rows if row["zero_reward"]]

    fieldnames = [
        "epoch",
        "participant_id",
        "reported_address",
        "claimed",
        "inference_count",
        "missed_requests",
        "miss_rate",
        "earned_coins",
        "rewarded_coins",
        "validation_weight",
        "full_weight",
        "confirmation_weight",
        "raw_total",
        "chain_effective_weight_uncapped",
        "chain_effective_weight",
        "total_epoch_weight",
        "fixed_epoch_reward",
        "expected_reward_pre_downtime",
        "preliminary_exposure",
        "zero_reward",
        "zero_reward_claimed",
        "needs_root_cause_review",
    ]

    write_csv(out_dir / "participants_269_272.csv", all_rows, fieldnames)
    write_csv(out_dir / "epoch_272_reported_and_claimed_zero_reward.csv", interesting_rows, fieldnames)
    write_csv(out_dir / "zero_reward_269_272.csv", zero_reward_rows, fieldnames)
    write_csv(
        out_dir / "epoch_summary_269_272.csv",
        aggregates,
        [
            "epoch",
            "participant_count",
            "zero_reward_count",
            "zero_reward_claimed_count",
            "reported_address_count",
            "reported_zero_reward_count",
            "total_inference_count",
            "total_missed_requests",
            "total_earned_coins",
            "total_rewarded_coins",
            "fixed_epoch_reward",
            "total_epoch_weight",
            "power_capping_applied",
            "reported_preliminary_exposure",
            "claimed_zero_reward_preliminary_exposure",
        ],
    )

    report = {
        "case_id": "P3-CAND-01",
        "epochs": args.epochs,
        "reported_addresses": sorted(REPORTED_ADDRESSES),
        "aggregates": aggregates,
        "epoch_272_reported_and_claimed_zero_reward": interesting_rows,
        "notes": [
            "preliminary_exposure is not approved compensation",
            "chain_effective_weight is computed from release/v0.2.12 chain settlement logic before downtime",
            "full_weight and confirmation_weight come from parent epoch_group_data",
            "raw_total comes from model subgroup epoch_group_data ML node poc_weight values with model weight_scale_factor",
            "no manual participant weight overrides are used",
            "root cause requires retained devshard proof/stat data",
        ],
    }
    (out_dir / "analysis_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    print(json.dumps(report["aggregates"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
