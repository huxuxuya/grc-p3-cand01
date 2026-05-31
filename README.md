# P3-CAND-01: High Miss Rate / Devshard Issue

GRC case intake form and reproducible investigation package for Proposal #3
candidate `P3-CAND-01`.

Plain-language summary: in epoch 272, six reported participants did real work
and had non-zero `earned_coins`, but their fixed reward became `0` because the
settlement path counted a high miss rate. The outcome is confirmed on-chain.
The likely area is devshard validation/recovery under heavy long-input traffic,
but final protocol liability still needs independent devshard validation.
Compensation is not approved here; payout numbers are technical estimates.

## 1. Case Basics

| Field | Answer |
| --- | --- |
| Case ID | P3-CAND-01 |
| Short title | High Miss Rate / Devshard Issue |
| Reporter / proposer | Votkon; technical reports by Nik |
| Date opened (UTC) | 2026-05-23 |
| Related links | [Audit/calculation repository](https://github.com/huxuxuya/gonka_248_and_250_-epoch_loss/); [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md); [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) |
| Affected epoch(s) / block range | Epochs 269-272 reviewed; main reported incident is epoch 272. Epoch 272 block range from chain data: PoC start `4197707`, effective `4198107`, last `4213497`. |
| Affected software version(s) | Under investigation. Related changes are reported in `v0.2.13`, but a case-specific fix is not established. |
| Fix / patch reference | [PR #1143: v0.2.13 microrelease](https://github.com/gonka-ai/gonka/pull/1143); settlement reference: [`accountsettle.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/accountsettle.go), [`bitcoin_rewards.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/bitcoin_rewards.go). |

## 2. Short Summary

| Question | Answer |
| --- | --- |
| What happened? | Six reported epoch 272 addresses worked, claimed, had `earned_coins > 0`, but received `rewarded_coins = 0`. Their miss rates were about 12.88%-35.71%. |
| Why might restitution be needed? | If devshard data shows those misses came from a protocol/devshard issue, the zeroed fixed reward may be compensable. |
| Who may be affected? | The six reported addresses are confirmed. One additional claimed zero-reward address needs manual review. |
| What is already confirmed? | The on-chain reward outcome, counts, weights, miss rates, and payout estimates are reproduced in `artifacts/`. |
| What is still uncertain? | Final root cause, compensation eligibility, and whether PR #1143 is the exact fix. |

### Plain-Language Incident Narrative

In simple terms: these participants were not simply offline or absent. They did
work, but the epoch settlement treated their miss rate as too high and zeroed
their fixed reward. The lost fixed reward was not redistributed to other
participants; under the current settlement logic it remains as governance
remainder.

The devshard exports show that epoch 272 was abnormal: many very long inputs,
many `valid=false` validation rows, and hundreds of timeout txs. For the six
reported addresses, the strongest direct evidence is not direct timeout of
their own executions; it is their participation in a noisy validation
environment followed by a high miss-rate reward outcome.

Current conclusion: the reward outcome is real and reproduced. The root cause
is still not fully closed.

## 3. Timeline

Use UTC times. Original UTC+03 timestamps are retained in
[sources/P3-CAND-01-devops-chat.md](sources/P3-CAND-01-devops-chat.md).

| Event | Epoch | Block | Time (UTC) | Source / link | Notes |
| --- | --- | --- | --- | --- | --- |
| Issue starts / suspected affected window begins | 269 |  | 2026-05-23 | User-provided case description | Epochs 269-272 were included in preliminary review. |
| Reported six-address incident | 272 |  | 2026-05-23 08:53 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Nik reported six epoch 272 addresses with `work_coins` but no `reward_coins`; high miss rate was identified as the immediate outcome. |
| Claimant statement | 272 |  | 2026-05-23 09:02 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Claimant `A` reported their address was in the list and stated there were no outages. |
| Case proposed for Proposal #3 | 269-272 |  | 2026-05-23 10:12 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Votkon asked to add the case to Proposal #3 review. |
| Preliminary loss estimate | 269-272 |  | 2026-05-23 21:12 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Estimate only; not approved compensation. |
| Root cause explicitly unresolved | 269-272 |  | 2026-05-23 21:14 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Fedor Tmkhv: true cause unknown. |
| Operator-level technical hypothesis | 272 |  | 2026-05-24 04:10 | [DevOps chat evidence](sources/P3-CAND-01-devops-chat.md) | Nik reported abnormal miss rate and a long-input validation error example. |
| Related microrelease deployed |  |  | 2026-05-26 | [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) | Related `v0.2.13` changes; not established as case-specific remediation. |

## 4. Initial Technical Claim

| Question | Answer |
| --- | --- |
| What should have happened? | Participants with valid work and eligible validation weight should receive fixed reward proportional to eligible weight, unless reduced by protocol rules such as downtime/miss-rate punishment. |
| What actually happened? | Six reported epoch 272 addresses had non-zero work/earned coins and zero fixed reward. Chain data also shows a seventh `claimed=true` zero-reward address outside the reported six. |
| What component caused or may have caused it? | Immediate mechanism: downtime/binomial miss-rate outcome. Possible underlying area: retained devshard proof/stat data, validation stats, long-input validation behavior, or operator conditions. |
| What commit, release, config, or migration is involved? | Related context: PR #1143 / `v0.2.13` includes devshard storage, stats, and settlement-limit changes. This repository does not establish it as the root-cause fix. |
| Is the issue fixed? | Unknown for this case. The on-chain outcome is reproduced; root-cause proof is still required. |

## 5. Affected Scope

| Question | Answer |
| --- | --- |
| Affected participant type(s) | Active epoch participants with work activity and high miss-rate / zero fixed reward outcomes. |
| Affected reward stream(s) | Fixed `rewarded_coins`; `earned_coins` / `work_coins` were still present for the reported six. |
| Affected model / subgroup, if relevant | Epoch 272 group models from chain data: `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`, `moonshotai/Kimi-K2.6`. |
| Affected rounds, CPoCs, or epochs | Epochs 269-272 reviewed; main reported incident is epoch 272. |
| Baseline state to compare against | Pre-downtime fixed reward share: `validation_weight / total_epoch_weight * fixed_epoch_reward`. This is a technical exposure estimate, not an approved payout formula. |
| Estimated affected count | Epoch 272: 6 reported addresses; 7 `claimed=true` zero-reward addresses; 14 total zero-reward outcomes. |
| Estimated restitution exposure | Reported six: `35,492.857904723 GNK`. All epoch 272 claimed zero-reward rows: `35,629.817378568 GNK`. These are technical estimates, not approved payouts. |

Display note: GNK values use `1 GNK = 1,000,000,000` chain integer units.

Epoch-level reproduction:

| Epoch | Participants | Zero reward | Claimed zero reward | Reported addresses present | Reported zero reward | Total inference | Missed requests | Total rewarded GNK | Reported preliminary exposure GNK |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 269 | 58 | 12 | 1 | 4 | 0 | 72438 | 1334 | 228,007.006768336 | 210.552884273 |
| 270 | 49 | 5 | 0 | 5 | 0 | 327454 | 863 | 265,454.382163070 | 1,993.651514223 |
| 271 | 49 | 7 | 0 | 5 | 0 | 123406 | 2822 | 236,273.187242554 | 9,340.681041098 |
| 272 | 50 | 14 | 7 | 6 | 6 | 20405 | 855 | 170,919.558595844 | 35,492.857904723 |

Epoch 272 reported and additional claimed zero-reward rows:

| Address | Reported six | Inference | Missed | Miss rate | Earned coins | Rewarded GNK | Validation weight | Preliminary exposure GNK |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | yes | 309 | 90 | 22.56% | 5262646 | 0 | 25462 | 8,784.035574445 |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | yes | 308 | 59 | 16.08% | 10348054 | 0 | 17297 | 5,967.224229486 |
| `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw` | yes | 416 | 72 | 14.75% | 7795716 | 0 | 20981 | 7,238.152949000 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | yes | 406 | 60 | 12.88% | 6778606 | 0 | 21124 | 7,287.485958471 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | yes | 185 | 50 | 21.28% | 2268162 | 0 | 11782 | 4,064.625997098 |
| `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n` | yes | 63 | 35 | 35.71% | 2019169 | 0 | 6236 | 2,151.333196223 |
| `gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` | no | 68 | 23 | 25.27% | 89061 | 0 | 397 | 136.959473845 |

## 6. Eligibility Draft

These rules are only a starting point. Eligibility cannot be finalized until
root cause is established.

### Include Participants Who

| Rule | Reason / source |
| --- | --- |
| Were in epoch 272 and match the six reported DevOps addresses | Direct case report and on-chain confirmation in `artifacts/epoch_272_reported_and_claimed_zero_reward.csv`. |
| Had non-zero `earned_coins`, `rewarded_coins = 0`, and `claimed = true` | Shows work was settled but fixed reward was zeroed. |
| Can be tied to retained devshard proof/stat evidence showing protocol-side or devshard-side cause | Required to move from technical exposure to compensation eligibility. |

### Exclude Participants Who

| Rule | Reason / source |
| --- | --- |
| Had `rewarded_coins > 0` | No zero fixed-reward outcome for this incident. |
| Had zero reward because they did not claim or had no work/eligible activity | Different condition from the reported incident. |
| Cannot be tied to protocol/devshard root cause after retained data review | Current evidence does not establish protocol liability. |

### Needs Manual Review

| Case type | Why it is ambiguous |
| --- | --- |
| `gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` | It is `claimed=true`, has non-zero `earned_coins`, and zero reward in epoch 272, but was not in the reported six. |
| Epochs 269-271 reported-address exposure | Reported addresses appear in earlier epochs, but the main case evidence is epoch 272. |
| Any address with high misses but `claimed=false` | Zero reward may be expected if settlement was not claimed or a different state applies. |

## 7. Evidence Needed

| Evidence | Location / command / endpoint | Status |
| --- | --- | --- |
| Chain data source | `data/raw/*.json`; fetched from `node1.gonka.ai` | Collected for epochs 269-272. |
| Historical query method | `python3 scripts/fetch_case_data.py --epochs 269 270 271 272` | Implemented. |
| Relevant code / commits | [`bitcoin_rewards.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/bitcoin_rewards.go), [`accountsettle.go`](https://github.com/gonka-ai/gonka/blob/17808620293b57112896bcbb7f99c4c2f554d6c8/inference-chain/x/inference/keeper/accountsettle.go), [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) | Referenced; root-cause link not established. |
| Release or deployment timestamps | `v0.2.13` reported deployed 2026-05-26 | Needs confirmation from release/deployment source if used as evidence. |
| Operator reports, if any | [sources/P3-CAND-01-devops-chat.md](sources/P3-CAND-01-devops-chat.md) | Recorded from case description. |
| Existing scripts, CSVs, or JSON files | `scripts/`, `data/raw/`, `artifacts/` | Added. |
| Retained devshard proof/stat data | `scripts/fetch_devshard_stats.py`; `artifacts/devshard_host_stats_audit.csv`; `data/raw/devshard/` | Queried for zero-reward rows. No epoch 269-272 host stats were retained on-chain at query time. Required external archives remain missing. |
| Devshard settlement events | `data/devshard_settlements.ndjson`; `artifacts/devshard_settlement_events_summary.csv` | 48 settlement events found in epoch 272 block range, but they are event-level records without `host_stats`, signatures, or full tx payloads. |

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

This does not mean devshard evidence never existed. It means the current on-chain
query endpoint cannot recover it for this case. The next required evidence must
come from archived devshard logs, settlement transaction payloads with
`host_stats`, retained proof bundles, or an old state snapshot taken before
pruning. See [sources/devshard-investigation.md](sources/devshard-investigation.md).

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
`100,000`. This supports a long-input / validation-failure environment, but the
exact protocol-liability conclusion still requires policy and root-cause review.

## 8. Draft Restitution Method

| Question | Answer |
| --- | --- |
| What baseline will be used? | Technical exposure baseline: pre-downtime fixed reward share using validation weight and total epoch weight. |
| Why is that baseline fair? | It estimates the fixed reward share before the high miss-rate outcome zeroed the participant's reward. It is useful for investigation, but not enough for approval. |
| What denominator will be used? | `total_epoch_weight` from `epoch_group_data`; epoch 272 value is `823183`. |
| Should actual rewards already received be subtracted? | Yes for exposure calculations: `max(baseline_reward_pre_downtime - rewarded_coins, 0)`. For the reported six, `rewarded_coins = 0`. |
| Should partial payouts stay eligible? | Policy decision required. This repo does not approve payouts. |
| Should downtime, misses, invalidation, or slashing affect eligibility? | Yes, they must be analyzed. The immediate zero-reward path is high miss rate, but root cause must decide whether it is compensable. |
| Should the calculation include only fixed rewards or other losses too? | Current calculation covers fixed `rewarded_coins` exposure only. `earned_coins` are reported separately. |

Formula draft:

```text
fixed_epoch_reward = floor(initial_epoch_reward * exp(decay_rate) ^ (epoch - genesis_epoch))
baseline_reward_pre_downtime = floor(validation_weight * fixed_epoch_reward / total_epoch_weight)
preliminary_exposure = max(baseline_reward_pre_downtime - rewarded_coins, 0)
```

Units and rounding:

| Item | Answer |
| --- | --- |
| Internal unit | Chain integer coin units from API responses. |
| Display unit | GNK in README payout tables; `1 GNK = 1,000,000,000` chain integer units. Raw CSV/JSON artifacts keep chain integers. |
| Rounding rule | Integer floor division, matching settlement-style integer reward allocation. |
| Final payout precision | Not decided; compensation is not approved. |

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
- Per-participant restitution table: preliminary exposure table in `artifacts/epoch_272_reported_and_claimed_zero_reward.csv`.
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
| `artifacts/analysis_summary.json` | Machine-readable summary. |
| `artifacts/devshard_host_stats_audit.csv` | Devshard stats availability audit for zero-reward rows. |
| `artifacts/devshard_host_stats_summary.json` | Devshard retention summary. |
| `artifacts/devshard_epoch_272_ndjson_summary.json` | Stream analysis of large devshard exports for epoch 272. |
| `artifacts/devshard_epoch_272_decoded_txs_summary.json` | Decoded protobuf devshard tx summary for epoch 272. |
| `artifacts/devshard_epoch_272_case_causality_summary.csv` | Linked case-address causality summary by `escrow_id + inference_id`. |

## 10. Required Validator Checks

- Re-run the calculation or independently reproduce the totals.
- Independently analyze the devshard data and reach the same or clearly
  documented different conclusions.
- Check the root cause against code, release, deployment, and retained devshard evidence.
- Check inclusion and exclusion rules against raw data.
- Spot-check the largest preliminary exposure: `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4`.
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
| Should participants with misses or invalidations be included? | Not decided. Inclusion should depend on root-cause proof, not miss count alone. |
| How should ambiguous cases be handled? | Manual review, especially the seventh claimed zero-reward address not in the reported six. |
| Which loss types are in scope? | Current artifacts cover fixed reward exposure only. |
| Should restitution use approximation or full recomputation? | Full recomputation is preferred if retained devshard/stat data can establish corrected eligibility. |
| Does high miss rate by itself prove protocol liability? | No. It proves the immediate reward outcome, not the underlying cause. |
| Is PR #1143 a case-specific fix? | Unknown. Treat as related context until root-cause evidence links it to this incident. |
| Can current on-chain devshard stats close epoch 272 root cause? | No. The endpoint returns `found=false` for the case targets; the data is likely pruned. |

## 12. Conflict Check

Complete before assigning people.

| Question | Answer |
| --- | --- |
| Does the proposed investigator benefit from the case? | Unknown; must be confirmed by GRC. |
| Does the proposed validator benefit from the case? | Unknown; must be confirmed by GRC. |
| Did either person work on the faulty component? | Unknown because faulty component is not established. |
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
