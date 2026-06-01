# P3-CAND-01: High Miss Rate / Devshard Issue, Epoch 272

| Field | Value |
|---|---|
| **Case** | `P3-CAND-01` - High Miss Rate / Devshard Issue |
| Epochs affected | Main incident: epoch `272`. Reviewed: `269-280`. |
| Affected participants | 6 confirmed reported addresses. 1 additional claimed zero-reward address remains manual review. |
| Estimated compensation | Reported six: `35,040.581153560 GNK`. All epoch 272 claimed zero-reward rows: `35,109.923355683 GNK`. |
| **Cause and evidence** | Most likely devshard / validation accounting failure under heavy long-input traffic. Evidence: [detailed report](DETAILED_README.md), [devshard notes](sources/devshard-investigation.md), [case table](artifacts/epoch_272_reported_and_claimed_zero_reward.csv), [decoded tx summary](artifacts/devshard_epoch_272_decoded_txs_summary.json). |
| **Can it happen again?** | No known repeat path in checked epochs `273-280`; the same `claimed=true` + zero fixed reward pattern did not recur for reported addresses. |
| **Mitigation / fix** | Likely related fix area: `v0.2.13`, applied on-chain at height `4267300` on `2026-05-26 14:39:41 UTC`; [PR #1143](https://github.com/gonka-ai/gonka/pull/1143) merged at `2026-05-26 18:59:21 UTC`. Exact one-to-one proof is limited by pruned epoch 272 data. |
| **Compensation overlap** | No known overlap. This calculation covers fixed `rewarded_coins` exposure only. |
| **Current decision** | GRC should decide whether to approve compensation for the six confirmed addresses using the chain-derived effective-weight estimate below. |
| **Review focus** | Validator: `@mikenosov`. Re-check the devshard-based proof first: exports, decoded txs, linked causality rows, computed `chain_effective_weight`, GNK conversion, and post-272 non-recurrence. |

## Summary

In epoch 272, six reported participants worked, claimed the epoch, earned
`earned_coins`, but received `rewarded_coins = 0` after a high miss-rate
settlement outcome. The audit found those same addresses in devshard activity
and found an abnormal epoch 272 environment: very long inputs, many false
validations, and hundreds of timeout transactions.

The evidence fits a devshard / validation-path issue better than ordinary
operator downtime. The participants appear to have performed honest work; their
own executed inferences do not show direct timeout txs in the decoded devshard
link.

This conclusion is based on devshard data, not only on the chain reward table:
local devshard exports were decoded, linked by `escrow_id + inference_id`, and
cross-checked against settlement events and per-address activity artifacts.

## Compensation Estimate

Values are shown in GNK. The estimate uses the effective reward weight from
chain settlement logic before the downtime zeroing. Epoch 272 settled on the
pre-`v0.2.13` reward path, so `chain_effective_weight` is reconstructed from
parent `weight` / `confirmation_weight` plus model subgroup `ml_nodes.poc_weight`
and `weight_scale_factor`; no participant weights are hardcoded.

| Address | Status | Effective weight | Compensation GNK |
|---|---|---:|---:|
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | confirmed | 25462 | 8,784.035574445 |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | confirmed | 16524 | 5,700.549989479 |
| `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw` | confirmed | 20981 | 7,238.152949000 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | confirmed | 21124 | 7,287.485958471 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | confirmed | 11782 | 4,064.625997098 |
| `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n` | confirmed | 5698 | 1,965.730685067 |
| **Confirmed total** | 6 addresses |  | **35,040.581153560** |
| `gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s` | manual review | 201 | 69.342202123 |
| **Total incl. manual review** | 7 addresses |  | **35,109.923355683** |

## Post-Incident Check

The same case pattern means: reported address + `claimed=true` +
`rewarded_coins = 0`. That did not recur in epochs `273-280`.

| Epoch | Reported addresses present | Reported claimed zero reward | Reported unclaimed zero reward | Case pattern reproduced |
|---|---:|---:|---:|---|
| 273 | 6 | 0 | 1 | No |
| 274 | 3 | 0 | 1 | No |
| 275 | 3 | 0 | 0 | No |
| 276 | 3 | 0 | 0 | No |
| 277 | 3 | 0 | 0 | No |
| 278 | 4 | 0 | 1 | No |
| 279 | 3 | 0 | 0 | No |
| 280 | 4 | 0 | 0 | No |

Rows in epochs `273`, `274`, and `278` with zero reward are different from the
case pattern: they are `claimed=false`, with no inference, missed request, or
earned-coin activity.

## Evidence Limits

The outcome and compensation math are reproducible from local artifacts. The
remaining limit is root-cause replay: current on-chain retention no longer has
epoch 272 devshard host stats or full settlement payloads with `host_stats`,
signatures, `state_root`, and `rest_hash`. That prevents 100% replay proof, but
does not change the confirmed on-chain reward outcome.

## Why v0.2.13 Likely Helped

The strongest relevant fixes in PR #1143 are the devshard ones:

| v0.2.13 change | Why it likely helped this case |
|---|---|
| Devshard validation and recovery edge-case fixes | Best match for the observed false-validation / missed-result behavior. |
| Devshard escrow nonce limit raised from `20,000` to `1,000,000` | Reduces the chance that a busy devshard epoch hits settlement limits. |
| `MaxEscrowsPerEpoch` raised to `500,000` | Gives settlement more room under high request volume. |

These are the most likely reasons the same pattern is not seen again after
epoch 272. Exact proof is limited because epoch 272 host stats and full
settlement payloads are pruned.

## Files

| File | Purpose |
|---|---|
| [DETAILED_README.md](DETAILED_README.md) | Full investigation narrative, evidence, calculations, and caveats. |
| [artifacts/epoch_272_reported_and_claimed_zero_reward.csv](artifacts/epoch_272_reported_and_claimed_zero_reward.csv) | Main compensation table. |
| [artifacts/post_incident_epoch_summary_273_280.csv](artifacts/post_incident_epoch_summary_273_280.csv) | Post-incident recurrence check. |
| [sources/devshard-investigation.md](sources/devshard-investigation.md) | Devshard data notes and root-cause evidence. |
