# Devshard Investigation Notes

## What is available on-chain

The Gonka chain exposes these devshard-related query endpoints:

- `/productscience/inference/inference/devshard_escrow/{id}`
- `/productscience/inference/inference/devshard_host_epoch_stats/{epoch_index}/{participant}`

The host epoch stats shape is:

| Field | Meaning |
| --- | --- |
| `participant` | Host participant address. |
| `epoch_index` | Epoch where stats were aggregated. |
| `missed` | Devshard missed count. |
| `invalid` | Devshard invalid count. |
| `cost` | Devshard cost attributed to the host. |
| `required_validations` | Required validation count. |
| `completed_validations` | Completed validation count. |
| `escrow_count` | Count of devshard escrows involving the host. |

## Retention finding

For `P3-CAND-01`, the query was run against all zero-reward rows from epochs
269-272. The result was:

| Item | Value |
| --- | ---: |
| Current epoch at query time | 281 |
| Targets queried | 38 |
| Stats found | 0 |
| Stats not found | 38 |
| Targets likely pruned | 38 |
| Devshard retention threshold | 2 epochs |

Raw responses are stored in `data/raw/devshard/`. The summary is stored in
`artifacts/devshard_host_stats_summary.json`, and the per-target audit is stored
in `artifacts/devshard_host_stats_audit.csv`.

## Code basis

Source inspection shows devshard stats are cleared by the devshard pruner after
the retention threshold:

- `DevshardPruningThreshold = 2`
- `DevshardHostEpochStatsMap.Clear(...)` is called in the devshard pruner
  post-prune hook.

Relevant upstream files:

- `inference-chain/proto/inference/inference/query.proto`
- `inference-chain/proto/inference/inference/devshard_escrow.proto`
- `inference-chain/x/inference/keeper/query_devshard_host_stats.go`
- `inference-chain/x/inference/keeper/devshard_host_stats.go`
- `inference-chain/x/inference/keeper/devshard_pruning.go`
- `inference-chain/x/inference/keeper/pruning.go`

## Impact on this case

The on-chain devshard host stats endpoint cannot currently prove or disprove
the epoch 272 root cause because the relevant retained stats are no longer
available there. The case therefore needs one of:

- archived devshard node logs,
- archived settlement messages / transaction payloads with `host_stats`,
- off-chain retained devshard proof bundles,
- or an independently preserved chain state snapshot from before pruning.

Without one of those sources, the investigation can confirm reward outcomes and
miss rates but cannot close protocol liability.

## Large Devshard NDJSON Exports

Additional local exports were found:

| File | Rows | Contents |
| --- | ---: | --- |
| `data/devshard_diffs.ndjson` | 793992 | Raw signed devshard diffs / tx bundles in base64. |
| `data/devshard_inferences.ndjson` | 759932 | Inference-level records with executor, model, cost, status, token counts, and input length. |
| `data/devshard_validations.ndjson` | 435586 | Validation-level rows with validator address, slot, validity, inference id, and nonce. |
| `data/devshard_settlements.ndjson` | 89 | Settlement events. |

These files do help the case materially. They provide the off-chain / retained
devshard layer that the current chain query no longer retains.

For epoch 272:

| Metric | Value |
| --- | ---: |
| Devshard inference rows | 19764 |
| Validation rows | 4959 |
| Diff rows | 21693 |
| Decoded tx rows | 50008 |
| Settlement events | 63 |
| Execution timeouts | 812 |
| Refusal timeouts | 45 |
| False validation txs | 3649 |
| True validation txs | 1314 |
| Max claimed input length | 853165 |
| Inputs above 100000 chars/tokens as claimed field | 2734 |
| Inputs above 500000 | 149 |

The six reported epoch 272 addresses are present in the devshard exports as
executors and validators. Their validation rows are mostly `valid=false`:

| Address | Executed | Validation rows | Valid false | Valid true |
| --- | ---: | ---: | ---: | ---: |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | 63 | 23 | 20 | 3 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | 62 | 29 | 26 | 3 |
| `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw` | 46 | 34 | 34 | 0 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | 21 | 11 | 11 | 0 |
| `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n` | 15 | 11 | 8 | 3 |
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | 56 | 22 | 18 | 4 |

The additional on-chain similar address
`gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` does not appear in these epoch
272 devshard inference/validation exports, so it should stay in manual review.

Generated files:

- `artifacts/devshard_epoch_272_ndjson_summary.json`
- `artifacts/devshard_epoch_272_participant_activity.csv`
- `artifacts/devshard_epoch_272_case_executor_rows.csv`
- `artifacts/devshard_epoch_272_case_validation_rows.csv`
- `artifacts/devshard_epoch_272_decoded_txs.csv`
- `artifacts/devshard_epoch_272_decoded_txs_summary.json`

## Case Causality Link

Decoded txs were linked back to inference and validation rows using
`escrow_id + inference_id`.

For the six reported addresses, the direct signal is not execution timeouts on
their own executed inferences. The direct signal is false validations and long
inputs:

| Address | Executed | Executed with timeout | Executed validation false rows | Executed inputs >100k | Validator rows | Validator valid false |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | 63 | 0 | 28 | 10 | 23 | 20 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | 62 | 0 | 33 | 4 | 29 | 26 |
| `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw` | 46 | 0 | 18 | 12 | 34 | 34 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | 21 | 0 | 8 | 2 | 11 | 11 |
| `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n` | 15 | 0 | 6 | 1 | 11 | 8 |
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | 56 | 0 | 24 | 6 | 22 | 18 |

Across the six reported addresses:

- executed rows: 263
- executed rows with direct timeout tx: 0
- executed rows with input length above 100k: 35
- executed rows with at least one false validation: 98
- validator rows: 130
- validator `valid=false` rows: 117

Interpretation: the likely case chain is not "these six directly timed out as
executors". It is closer to "epoch 272 had a heavy long-input / false-validation
environment, and these six accumulated a bad validation/miss-rate outcome".

Generated files:

- `artifacts/devshard_epoch_272_case_causality_summary.csv`
- `artifacts/devshard_epoch_272_case_executor_causality.csv`
- `artifacts/devshard_epoch_272_case_validator_causality.csv`
- `artifacts/devshard_epoch_272_case_causality_summary.json`

## Settlement Event Data Found

`data/devshard_settlements.ndjson` contains 89 `devshard_escrow_settled`
events. These are useful but are not the full `MsgSettleDevshardEscrow`
payloads.

Available fields:

- `escrow_id`
- `block_height`
- `block_time`
- `settler`
- `version`
- `total_payout`
- `remainder`
- raw event attributes

Missing fields required for root-cause proof:

- `host_stats`
- `signatures`
- `state_root`
- `rest_hash`
- full transaction hash / decoded message payload

For epoch 272 block range, 48 settlement events were found. Their escrow ids are
between 1939 and 1986. Direct `devshard_escrow/{id}` queries for those 48 ids now
return `found=false`, so the escrow state is also pruned from current on-chain
query state.

Generated files:

- `artifacts/devshard_settlement_events_tagged.csv`
- `artifacts/devshard_settlement_events_summary.csv`
- `artifacts/devshard_settlement_events_summary.json`
