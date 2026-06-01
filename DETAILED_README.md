# P3-CAND-01: High Miss Rate / Devshard Issue

GRC case intake form and reproducible investigation package for Proposal #3
candidate `P3-CAND-01`.

Plain-language summary: in epoch 272, six reported participants did real work,
claimed the epoch, and had non-zero `earned_coins`, but their fixed reward was
settled as `0` after a high miss-rate outcome. The audit reproduces the on-chain
result, finds the same participants in retained devshard exports, and shows an
abnormal devshard environment with very long inputs, many false validations, and
hundreds of timeout transactions. The most likely explanation is a devshard /
validation-path issue triggered by heavy long-input traffic, not ordinary
operator downtime by the six reported participants. Related devshard storage,
stats, and settlement-limit changes shipped in `v0.2.13`; no equivalent
six-address zero-reward pattern has been found in later checked data. The only
remaining uncertainty is that some original epoch 272 devshard host stats and
full settlement payloads are pruned, so the exact causal chain cannot be
replayed with 100% certainty from current on-chain state.

## 1. Case Basics

| Field | Answer |
| --- | --- |
| Case ID | P3-CAND-01 |
| Short title | High Miss Rate / Devshard Issue |
| Reporter / proposer | Votkon; technical reports by Nik |
| Date opened (UTC) | 2026-05-23 |
| Related links | [Audit/calculation repository](https://github.com/huxuxuya/gonka_248_and_250_-epoch_loss/); [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md); [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) |
| Affected epoch(s) / block range | Epochs 269-272 reviewed; main reported incident is epoch 272. Epoch 272 block range from chain data: PoC start `4197707`, effective `4198107`, last `4213497`. |
| Affected software version(s) | Pre-`v0.2.13` behavior is the likely affected window. |
| Fix / patch reference | [PR #1143: v0.2.13 microrelease](https://github.com/gonka-ai/gonka/pull/1143) is the likely remediation area because it changes devshard storage, stats, and settlement limits. Settlement reference: [`accountsettle.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/accountsettle.go), [`bitcoin_rewards.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/bitcoin_rewards.go). |

## 2. Short Summary

| Question | Answer |
| --- | --- |
| What happened? | Six reported epoch 272 addresses worked, claimed, had `earned_coins > 0`, but received `rewarded_coins = 0`. Their miss rates were about 12.88%-35.71%. |
| Why might restitution be needed? | The evidence points to an abnormal devshard / validation environment rather than ordinary participant downtime. If GRC accepts that interpretation, the zeroed fixed reward is compensable. |
| Who may be affected? | The six reported addresses are confirmed as the main case. One additional claimed zero-reward address is similar on-chain but lacks matching devshard activity and stays in manual review. |
| What is already confirmed? | On-chain reward outcome, work/claim state, miss rates, devshard participation, long-input / false-validation environment, and chain-like payout estimates are reproduced in `artifacts/`. |
| What is still uncertain? | The exact per-slot devshard host stats and full settlement payloads for epoch 272 are no longer available from current on-chain retention, so the final causal replay cannot be made cryptographically complete. |

### Audit Conclusion

The case is sufficiently investigated for a practical GRC decision:

| Finding | Audit result | Source |
| --- | --- | --- |
| The six reported participants did work | Confirmed. All six had non-zero `earned_coins`, were `claimed=true`, and are present in epoch 272 chain data. | `artifacts/epoch_272_reported_and_claimed_zero_reward.csv` |
| They received no fixed reward | Confirmed. All six have `rewarded_coins = 0`. | `artifacts/epoch_272_reported_and_claimed_zero_reward.csv` |
| They were present in devshard activity | Confirmed. The six reported addresses appear as executors and validators in epoch 272 devshard exports. | `artifacts/devshard_epoch_272_participant_activity.csv`, `sources/devshard-investigation.md` |
| The epoch 272 devshard environment was abnormal | Confirmed. Decoded txs show `50,008` tx rows, `857` timeout txs, `3,649` false validation txs, and max claimed input length `853,165`. | `artifacts/devshard_epoch_272_decoded_txs_summary.json` |
| The participants look honest in this audit | Supported. They executed work, claimed the epoch, earned work coins, and the direct devshard link does not show execution timeouts on their own executed inferences. | `artifacts/devshard_epoch_272_case_causality_summary.json` |
| The issue appears fixed / not repeating | Supported by available data. `v0.2.13` changed the relevant devshard and settlement areas, and later checked devshard data does not show the same six-address zero-reward incident pattern. | [PR #1143](https://github.com/gonka-ai/gonka/pull/1143), `artifacts/recent_devshard_host_stats_summary.json` |
| 100% replay proof is available | No. Current on-chain retention no longer contains epoch 272 host stats or full devshard settlement payloads. | `artifacts/devshard_host_stats_summary.json`, `sources/devshard-investigation.md` |

Important: the audit conclusion is based on devshard evidence, not only on a
reward-table comparison. The investigation decoded local devshard exports,
linked inference and validation rows by `escrow_id + inference_id`, checked
settlement events, and then compared those findings with the chain reward
outcome.

### Plain-Language Incident Narrative

In simple terms: these participants were not simply offline or absent. They
showed up in the epoch, did useful work, claimed the epoch, and received
`earned_coins`. The fixed reward became zero because the settlement path saw a
miss-rate result high enough to remove the reward.

The most likely story is this: epoch 272 had unusually heavy devshard traffic,
including very long inputs and a large number of false validation outcomes.
That created a noisy validation/recovery environment. The six reported
participants were active inside that environment, and the final settlement
classified them with high misses even though the decoded devshard link does not
show their own executed inferences directly timing out. In other words, the
available evidence fits a devshard / validation accounting failure much better
than it fits six independent operators all failing at the same time.

The lost fixed reward was not redistributed to other participants. Under the
settlement logic it remained as governance remainder, which is why a restitution
calculation can be made without taking rewards away from other operators.

## 3. Timeline

Use UTC times. Original UTC+03 timestamps are retained in
[sources/P3-CAND-01-devops-chat.md](sources/P3-CAND-01-devops-chat.md).

| Event | Epoch | Block | Time (UTC) | Source / link | Notes |
| --- | --- | --- | --- | --- | --- |
| Issue starts / suspected affected window begins | 269 |  | 2026-05-23 | User-provided case description | Epochs 269-272 were included in preliminary review. |
| Epoch 272 PoC start block | 272 | 4197707 | 2026-05-22 09:32:39 | Chain block query: `/cosmos/base/tendermint/v1beta1/blocks/4197707` | Start boundary for the main incident epoch. |
| Epoch 272 effective block | 272 | 4198107 | 2026-05-22 10:07:37 | Chain block query: `/cosmos/base/tendermint/v1beta1/blocks/4198107` | Epoch 272 became effective. |
| Epoch 272 devshard settlements observed | 272 | 4213209-4213251 | 2026-05-23 08:03:35-08:07:14 | `artifacts/devshard_settlement_events_tagged.csv` | 48 settlement events in the epoch 272 block range. |
| Epoch 272 last block in chain data | 272 | 4213497 | 2026-05-23 08:28:48 | Chain block query: `/cosmos/base/tendermint/v1beta1/blocks/4213497` | End boundary used for this investigation. |
| Reported six-address incident | 272 |  | 2026-05-23 08:53 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Nik reported six epoch 272 addresses with `work_coins` but no `reward_coins`; high miss rate was identified as the immediate outcome. |
| Claimant statement | 272 |  | 2026-05-23 09:02 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Claimant `A` reported their address was in the list and stated there were no outages. |
| Case proposed for Proposal #3 | 269-272 |  | 2026-05-23 10:12 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Votkon asked to add the case to Proposal #3 review. |
| Preliminary loss estimate | 269-272 |  | 2026-05-23 21:12 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Early estimate; replaced by the chain-like GNK estimates in this README. |
| Root cause explicitly unresolved | 269-272 |  | 2026-05-23 21:14 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Fedor Tmkhv: true cause unknown. |
| Operator-level technical hypothesis | 272 |  | 2026-05-24 04:10 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Nik reported abnormal miss rate and a long-input validation error example. |
| `v0.2.13` applied on-chain |  | 4267300 | 2026-05-26 14:39:41 | Chain upgrade query: `/cosmos/upgrade/v1beta1/applied_plan/v0.2.13` | Chain reports applied plan height `4267300`; block timestamp confirms when the upgrade took effect on-chain. |
| PR #1143 merged |  |  | 2026-05-26 18:59:21 | [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) | GitHub merge for `v0.2.13` microrelease; likely remediation area. |

## 4. Initial Technical Claim

| Question | Answer |
| --- | --- |
| What should have happened? | Participants with valid work and eligible validation weight should receive fixed reward proportional to eligible weight, unless reduced by protocol rules such as downtime/miss-rate punishment. |
| What actually happened? | Six reported epoch 272 addresses had non-zero work/earned coins and zero fixed reward. Chain data also shows a seventh `claimed=true` zero-reward address outside the reported six. |
| What component caused or may have caused it? | Immediate mechanism: downtime/binomial miss-rate outcome. Likely underlying area: devshard validation/recovery and settlement accounting under heavy long-input traffic. |
| What commit, release, config, or migration is involved? | PR #1143 / `v0.2.13` is the relevant remediation area because it includes devshard storage, stats, and settlement-limit changes. |
| Is the issue fixed? | The same pattern has not been found in later checked data, and the related remediation shipped in `v0.2.13`. Exact proof that PR #1143 alone fixed this case is not possible from current retained data. |

## 5. Affected Scope

| Question | Answer |
| --- | --- |
| Affected participant type(s) | Active epoch participants with work activity and high miss-rate / zero fixed reward outcomes. |
| Affected reward stream(s) | Fixed `rewarded_coins`; `earned_coins` / `work_coins` were still present for the reported six. |
| Affected model / subgroup, if relevant | Epoch 272 group models from chain data: `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`, `moonshotai/Kimi-K2.6`. |
| Affected rounds, CPoCs, or epochs | Epochs 269-272 reviewed; main reported incident is epoch 272. |
| Baseline state to compare against | Chain-like pre-downtime reward: `chain_effective_weight / total_epoch_weight * fixed_epoch_reward`. Raw `validation_weight` exposure is retained only as an upper technical reference. |
| Estimated affected count | Epoch 272: 6 reported addresses; 7 `claimed=true` zero-reward addresses; 14 total zero-reward outcomes. |
| Estimated restitution exposure | Reported six: `30,715.490665898 GNK`. All epoch 272 claimed zero-reward rows: `30,784.832868021 GNK`. These are chain-like technical estimates pending GRC approval. |

Display note: GNK values use `1 GNK = 1,000,000,000` chain integer units.

Epoch-level reproduction:

| Epoch | Participants | Zero reward | Claimed zero reward | Reported addresses present | Reported zero reward | Total inference | Missed requests | Total rewarded GNK | Reported chain-like exposure GNK |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 269 | 58 | 12 | 1 | 4 | 0 | 72438 | 1334 | 228,007.006768336 | 210.552884273 |
| 270 | 49 | 5 | 0 | 5 | 0 | 327454 | 863 | 265,454.382163070 | 1,993.651514223 |
| 271 | 49 | 7 | 0 | 5 | 0 | 123406 | 2822 | 236,273.187242554 | 9,340.681041098 |
| 272 | 50 | 14 | 7 | 6 | 6 | 20405 | 855 | 170,919.558595844 | 30,715.490665898 |

Post-incident check: epochs 273-280 do not reproduce the case
pattern. The important column is `Reported claimed zero reward`: it stays `0`
for every checked epoch after 272. Epochs 273, 274, and 278 each have one
reported address with zero reward, but those rows are `claimed=false`, with no
inference, missed request, or earned-coin activity; they are not the same
condition as epoch 272. Machine-readable copy:
`artifacts/post_incident_epoch_summary_273_280.csv`.

| Epoch | Participants | Reported addresses present | All claimed zero reward | Reported claimed zero reward | Reported unclaimed zero reward | Total inference | Missed requests | Miss rate | Total rewarded GNK | Case pattern reproduced |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 273 | 61 | 6 | 0 | 0 | 1 | 0 | 0 | n/a | 239,304.384905834 | No |
| 274 | 55 | 3 | 0 | 0 | 1 | 2889 | 61 | 2.07% | 224,991.453021647 | No |
| 275 | 55 | 3 | 0 | 0 | 0 | 0 | 0 | n/a | 263,607.516076004 | No |
| 276 | 54 | 3 | 0 | 0 | 0 | 0 | 0 | n/a | 193,820.331174280 | No |
| 277 | 56 | 3 | 0 | 0 | 0 | 136874 | 744 | 0.54% | 265,479.872579124 | No |
| 278 | 57 | 4 | 0 | 0 | 1 | 68 | 0 | 0.00% | 234,407.151853392 | No |
| 279 | 57 | 3 | 0 | 0 | 0 | 360088 | 224 | 0.06% | 264,029.659614357 | No |
| 280 | 54 | 4 | 0 | 0 | 0 | 5982 | 180 | 2.92% | 266,519.341381703 | No |

Epoch 272 reported and additional claimed zero-reward rows:

| Address | Reported six | Inference | Missed | Miss rate | Earned coins | Rewarded GNK | Effective weight | Chain-like exposure GNK | Raw-weight reference GNK |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | yes | 309 | 90 | 22.56% | 5262646 | 0 | 21271 | 7,338.198912262 | 8,784.035574445 |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | yes | 308 | 59 | 16.08% | 10348054 | 0 | 15146 | 5,225.159170943 | 5,967.224229486 |
| `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw` | yes | 416 | 72 | 14.75% | 7795716 | 0 | 18750 | 6,468.489004039 | 7,238.152949000 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | yes | 406 | 60 | 12.88% | 6778606 | 0 | 18899 | 6,519.891929991 | 7,287.485958471 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | yes | 185 | 50 | 21.28% | 2268162 | 0 | 10661 | 3,677.896601176 | 4,064.625997098 |
| `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n` | yes | 63 | 35 | 35.71% | 2019169 | 0 | 4307 | 1,485.855047487 | 2,151.333196223 |
| `gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` | no | 68 | 23 | 25.27% | 89061 | 0 | 201 | 69.342202123 | 136.959473845 |

## 6. Eligibility Draft

These rules reflect the audit result. Final approval is still a GRC policy
decision, but the technical evidence supports including the six reported epoch
272 participants.

### Include Participants Who

| Rule | Reason / source |
| --- | --- |
| Were in epoch 272 and match the six reported DevOps addresses | Direct case report and on-chain confirmation in `artifacts/epoch_272_reported_and_claimed_zero_reward.csv`. |
| Had non-zero `earned_coins`, `rewarded_coins = 0`, and `claimed = true` | Shows the participants worked and claimed, but fixed reward was zeroed. |
| Are present in epoch 272 devshard exports as executors and validators | Confirms they were active in the devshard layer, not absent from the work path. |
| Fit the abnormal long-input / false-validation incident pattern | Supports compensation eligibility because the observed misses are consistent with the devshard incident environment. |

### Exclude Participants Who

| Rule | Reason / source |
| --- | --- |
| Had `rewarded_coins > 0` | No zero fixed-reward outcome for this incident. |
| Had zero reward because they did not claim or had no work/eligible activity | Different condition from the reported incident. |
| Cannot be tied to the epoch 272 devshard incident pattern after retained data review | Keeps compensation scoped to the investigated incident. |

### Needs Manual Review

| Case type | Why it is ambiguous |
| --- | --- |
| `gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` | It is `claimed=true`, has non-zero `earned_coins`, and zero reward in epoch 272, but was not in the reported six and does not appear in the local epoch 272 devshard inference/validation exports. |
| Epochs 269-271 reported-address exposure | Reported addresses appear in earlier epochs, but the main case evidence is epoch 272. |
| Any address with high misses but `claimed=false` | Zero reward may be expected if settlement was not claimed or a different state applies. |

## 7. Evidence And Limits

| Evidence | Location / command / endpoint | Status |
| --- | --- | --- |
| Chain data source | `data/raw/*.json`; fetched from `node1.gonka.ai` | Collected for epochs 269-272. |
| Historical query method | `python3 scripts/fetch_case_data.py --epochs 269 270 271 272` | Implemented. |
| Relevant code / commits | [`bitcoin_rewards.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/bitcoin_rewards.go), [`accountsettle.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/accountsettle.go), [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) | PR #1143 is the likely remediation area; exact one-to-one causal proof is limited by pruned data. |
| Release or deployment timestamps | `v0.2.13` reported deployed 2026-05-26 | Consistent with the incident not repeating in later checked data. |
| Operator reports, if any | [sources/P3-CAND-01-devops-chat.md](sources/P3-CAND-01-devops-chat.md) | Recorded from case description. |
| Existing scripts, CSVs, or JSON files | `scripts/`, `data/raw/`, `artifacts/` | Added. |
| Retained devshard proof/stat data | `scripts/fetch_devshard_stats.py`; `artifacts/devshard_host_stats_audit.csv`; `data/raw/devshard/` | Queried for zero-reward rows. No epoch 269-272 host stats were retained on-chain at query time; this is the main limit on 100% replay confidence. |
| Devshard settlement events | `data/devshard_settlements.ndjson`; `artifacts/devshard_settlement_events_summary.csv` | 48 settlement events found in epoch 272 block range, but they are event-level records without `host_stats`, signatures, or full tx payloads. |
| Effective settlement weights | `artifacts/epoch_272_reported_and_claimed_zero_reward.csv` column `chain_effective_weight` | Used for chain-like compensation estimates. Validator should independently verify these against available devshard / settlement data before approval. |

### Devshard Retention Finding

The chain exposes `devshard_host_epoch_stats/{epoch_index}/{participant}`, but
the case epochs are outside the current on-chain retention window. The audit
queried all 38 zero-reward rows from epochs 269-272:

| Item | Value |
| --- | ---: |
| Current epoch at query time | 281 |
| Devshard retention threshold | 2 epochs |
| Targets queried | 38 |
| Stats found | 0 |
| Stats not found | 38 |
| Targets likely pruned | 38 |

This does not weaken the confirmed on-chain outcome. It only limits the final
root-cause replay. Current on-chain query endpoints cannot recover the original
host stats for epoch 272; 100% reconstruction would require archived devshard
logs, full settlement transaction payloads with `host_stats`, retained proof
bundles, or an old state snapshot taken before pruning. See
[sources/devshard-investigation.md](sources/devshard-investigation.md).

Settlement event note: `data/devshard_settlements.ndjson` contains 89 settlement
events, 48 of which fall inside the epoch 272 block range. Those rows identify
escrow ids and payout/remainder totals, but they do not include slot-level
`host_stats`, signatures, `state_root`, or `rest_hash`. Direct
`devshard_escrow/{id}` queries for the 48 epoch 272 ids now return `found=false`.

Large NDJSON note: local devshard exports were found for diffs, inferences, and
validations. They materially improve the investigation. For epoch 272, decoded
devshard diffs contain `50,008` tx rows, including `857` timeouts, `812`
execution timeouts, `3,649` false validation txs, and very long input records
with max claimed input length `853,165`. The six reported addresses are present
in these devshard exports and have mostly `valid=false` validation rows. See
[sources/devshard-investigation.md](sources/devshard-investigation.md).

Case causality note: linking decoded txs to inference/validation rows by
`escrow_id + inference_id` shows the six reported addresses did not have direct
timeout txs on their own executed inferences. Their direct signal is false
validation rows plus long inputs: across the six addresses, `117` of `130`
validator rows are `valid=false`, `98` executed inferences have at least one
false validation, and `35` executed inferences have claimed input length above
`100,000`. This is the strongest practical explanation for the missed outcome:
the six were active, but they were operating inside a broken or overloaded
devshard validation environment.

Later-data note: current retained devshard stats for later checked epochs do
not show a repeat of this same six-address zero-reward pattern. Epoch 280 has
retained devshard stats for 30 participants with aggregate missed/invalid
counts, while epoch 279 is already outside the available retention window and
returns no host stats. This supports the conclusion that the incident is no
longer reproducing, while also showing why old devshard data must be archived
quickly for future cases.

## 8. Draft Restitution Method

| Question | Answer |
| --- | --- |
| What baseline will be used? | Chain-like expected fixed reward before the high miss-rate zeroing. |
| Why is that baseline fair? | It estimates what the chain would have paid if normal pre-downtime effective-weight logic applied and only the abnormal zeroing were removed. |
| What denominator will be used? | `total_epoch_weight` from `epoch_group_data`; epoch 272 value is `823183`. |
| Should actual rewards already received be subtracted? | Yes: `max(chain_expected_reward_pre_downtime - rewarded_coins, 0)`. For the reported six, `rewarded_coins = 0`. |
| Should partial payouts stay eligible? | Policy decision required by GRC. |
| Should downtime, misses, invalidation, or slashing affect eligibility? | Yes. For this case, the misses are treated as part of the abnormal devshard incident rather than a standalone operator-fault signal. |
| Should the calculation include only fixed rewards or other losses too? | Current calculation covers fixed `rewarded_coins` exposure only. `earned_coins` are reported separately. |

Formula draft:

```text
fixed_epoch_reward = floor(initial_epoch_reward * exp(decay_rate) ^ (epoch - genesis_epoch))
chain_expected_reward_pre_downtime = floor(chain_effective_weight * fixed_epoch_reward / total_epoch_weight)
preliminary_exposure = max(chain_expected_reward_pre_downtime - rewarded_coins, 0)
```

Raw-weight reference:

```text
raw_weight_reference = floor(validation_weight * fixed_epoch_reward / total_epoch_weight)
```

The raw-weight reference is useful for audit comparison, but it is not the
preferred payout estimate because it can exceed the reward that chain settlement
would have produced after normal effective-weight adjustments.

Units and rounding:

| Item | Answer |
| --- | --- |
| Internal unit | Chain integer coin units from API responses. |
| Display unit | GNK in README payout tables; `1 GNK = 1,000,000,000` chain integer units. Raw CSV/JSON artifacts keep chain integers. |
| Rounding rule | Integer floor division, matching settlement-style integer reward allocation. |
| Final payout precision | GRC approval pending; README values are technical GNK estimates. |

Reward flow note: fixed-reward settlement keeps pre-punishment weight in the
denominator. Downtime / miss-rate reductions are not redistributed to other
participants; they become governance remainder. In epoch 272, the reproduced
fixed epoch reward is `283,986.676469990 GNK`, total rewarded fixed reward is
`170,919.558595844 GNK`, and the estimated undistributed remainder is
`113,067.117874146 GNK`.

## 9. Required Investigator Output

The investigator should produce enough material for another person to rerun and
check the case.

- README with short summary and run instructions: present in this file.
- Reproducible script or notebook: `scripts/fetch_case_data.py`, `scripts/analyze_case.py`.
- Machine-readable output, preferably CSV and JSON: `artifacts/*.csv`, `artifacts/analysis_summary.json`.
- Per-participant restitution table: chain-like exposure table in `artifacts/epoch_272_reported_and_claimed_zero_reward.csv`.
- List of excluded and manual-review cases: included in sections 6 and 11.
- Narrative report with caveats: included in sections 2, 4, 5, and 8.
- At least one raw-data sanity check: epoch 272 count checks are listed below.

Run instructions:

```bash
python3 scripts/fetch_case_data.py --epochs 269 270 271 272
python3 scripts/analyze_case.py --epochs 269 270 271 272
python3 scripts/fetch_devshard_stats.py --targets-csv artifacts/zero_reward_269_272.csv
python3 scripts/analyze_devshard_settlements.py
python3 scripts/analyze_devshard_ndjson.py --epoch 272
python3 scripts/link_devshard_causality.py --epoch 272
```

The decoded protobuf tx artifact
`artifacts/devshard_epoch_272_decoded_txs.csv` is produced with the helper in
`scripts/p3decode_devshard_txs.go`. It must be run from a checkout of the Gonka
`devshard` Go module because it imports the module's generated protobuf types.

Generated outputs:

| File | Purpose |
| --- | --- |
| `artifacts/epoch_summary_269_272.csv` | Epoch-level counts and totals. |
| `artifacts/epoch_272_reported_and_claimed_zero_reward.csv` | Main incident table. |
| `artifacts/zero_reward_269_272.csv` | All zero-reward rows across reviewed epochs. |
| `artifacts/participants_269_272.csv` | Full participant-level table. |
| `artifacts/post_incident_epoch_summary_273_280.csv` | Post-incident check showing epochs 273-280 did not reproduce the case pattern. |
| `artifacts/analysis_summary.json` | Machine-readable summary. |
| `artifacts/devshard_host_stats_audit.csv` | Devshard stats availability audit for zero-reward rows. |
| `artifacts/devshard_host_stats_summary.json` | Devshard retention summary. |
| `artifacts/devshard_epoch_272_ndjson_summary.json` | Stream analysis of large devshard exports for epoch 272. |
| `artifacts/devshard_epoch_272_decoded_txs_summary.json` | Decoded protobuf devshard tx summary for epoch 272. |
| `artifacts/devshard_epoch_272_case_causality_summary.csv` | Linked case-address causality summary by `escrow_id + inference_id`. |

## 10. Required Validator Checks

- Re-run the calculation or independently reproduce the chain-like totals.
- Independently analyze the devshard data and reach the same or clearly
  documented different conclusions.
- Check the root cause against code, release, deployment, and retained devshard evidence.
- Check inclusion and exclusion rules against raw data.
- Verify `chain_effective_weight` values from devshard / settlement data, then confirm that the same payout estimates are reached.
- Spot-check the largest chain-like exposure: `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4`.
- Spot-check several smaller exposures, including `gonka1ce02...` and `gonka16xa2...`.
- Spot-check excluded or manual-review cases with `claimed=false`.
- Check formula, denominator, GNK conversion, units, and rounding.
- Confirm final report matches the GRC policy decision.

Expected sanity checks after running `scripts/analyze_case.py`:

| Check | Expected |
| --- | ---: |
| Epoch 272 participants | 50 |
| Epoch 272 zero-reward rows | 14 |
| Epoch 272 `claimed=true` zero-reward rows | 7 |
| Epoch 272 reported-address zero-reward rows | 6 |
| Epoch 272 total inference count | 20405 |
| Epoch 272 total missed requests | 855 |

## 11. GRC Policy Questions

| Question | Decision / link |
| --- | --- |
| Should partial rewards be subtracted? | Not decided. Current exposure formula subtracts actual `rewarded_coins`. |
| Should participants with misses or invalidations be included? | For this case, the six reported participants should be treated as eligible if GRC accepts the audit conclusion that epoch 272 misses came from the abnormal devshard validation environment. Miss count alone should not be enough for unrelated cases. |
| How should ambiguous cases be handled? | Manual review, especially the seventh claimed zero-reward address not in the reported six. |
| Which loss types are in scope? | Current artifacts cover fixed reward exposure only. |
| Should restitution use approximation or full recomputation? | Use the chain-like recomputation in this repo for the current decision. A fuller replay would be better, but current on-chain retention no longer has the original epoch 272 host stats and full settlement payloads. |
| Does high miss rate by itself prove protocol liability? | No. In this case, liability is supported by the combined evidence: honest work/claim state, devshard activity, long-input pressure, false validations, and non-repetition after the related fix. |
| Is PR #1143 a case-specific fix? | Most likely related and practically consistent with the incident stopping, but not provable as the only fix because epoch 272 host stats and full settlement payloads are pruned. |
| Can current on-chain devshard stats close epoch 272 root cause? | No. The endpoint returns `found=false` for the case targets; the data is pruned. The available NDJSON/devshard exports are enough for a practical audit conclusion, not a perfect replay. |

## 12. Conflict Check

Complete before assigning people.

| Question | Answer |
| --- | --- |
| Does the proposed investigator benefit from the case? | Unknown; must be confirmed by GRC. |
| Does the proposed validator benefit from the case? | Unknown; must be confirmed by GRC. |
| Did either person work on the faulty component? | Unknown. The likely technical area is devshard validation / settlement accounting, but personal conflict status is not recorded here. |
| Are any conflicts disclosed and accepted by GRC? | Not recorded in this repository. |

## 13. Ready For Assignment

- [x] Case basics are filled.
- [x] Time window is clear.
- [x] Initial technical claim is written.
- [x] Affected scope is described.
- [x] Eligibility draft is written.
- [x] Evidence sources are listed.
- [x] Draft restitution method is written.
- [x] Open policy questions are listed.
- [ ] Conflict check is complete.
- [ ] GRC agrees the case is ready to assign.

## 14. Assignment

Fill only after the checklist above is complete.

| Role | Name / handle | Date (UTC) | Notes |
| --- | --- | --- | --- |
| Investigator | @OpenMindedPerson |  | From case description. |
| Validator | @mikenosov |  | Validator should have access to the devshard data needed to independently verify the case and reproduce the conclusions. |

Expected completion date:

## Sources

- [Audit/calculation repository](https://github.com/huxuxuya/gonka_248_and_250_-epoch_loss/)
- [DevOps chat evidence log](sources/P3-CAND-01-devops-chat.md)
- [PR #1143: v0.2.13 microrelease](https://github.com/gonka-ai/gonka/pull/1143)
- [Settlement logic: `accountsettle.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/accountsettle.go)
- [Reward remainder logic: `bitcoin_rewards.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/bitcoin_rewards.go)
