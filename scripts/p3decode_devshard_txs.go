package main

// Helper for reproducing artifacts/devshard_epoch_272_decoded_txs.csv.
//
// Run this from a checkout of the Gonka devshard Go module, where
// import "devshard/types" is available. For example:
//
//   mkdir -p cmd/p3decode
//   cp /path/to/grc-p3-cand01/scripts/p3decode_devshard_txs.go cmd/p3decode/main.go
//   go run ./cmd/p3decode /path/to/devshard_inferences.ndjson /path/to/devshard_diffs.ndjson 272 /path/to/devshard_epoch_272_decoded_txs.csv

import (
	"bufio"
	"encoding/base64"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"strconv"

	types "devshard/types"
	"google.golang.org/protobuf/proto"
)

type DiffRow struct {
	EscrowID  int    `json:"escrow_id"`
	Nonce     uint64 `json:"nonce"`
	RawTxsB64 string `json:"raw_txs_b64"`
}

type InfRow struct {
	EscrowID   int `json:"escrow_id"`
	EpochIndex int `json:"epoch_index"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func loadEpochEscrows(path string, epoch int) map[int]bool {
	f, err := os.Open(path)
	must(err)
	defer f.Close()

	escrows := map[int]bool{}
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1024), 16*1024*1024)
	for sc.Scan() {
		var r InfRow
		must(json.Unmarshal(sc.Bytes(), &r))
		if r.EpochIndex == epoch {
			escrows[r.EscrowID] = true
		}
	}
	must(sc.Err())
	return escrows
}

func txKind(tx *types.DevshardTx) string {
	switch tx.GetTx().(type) {
	case *types.DevshardTx_StartInference:
		return "start_inference"
	case *types.DevshardTx_ConfirmStart:
		return "confirm_start"
	case *types.DevshardTx_FinishInference:
		return "finish_inference"
	case *types.DevshardTx_TimeoutInference:
		return "timeout_inference"
	case *types.DevshardTx_Validation:
		return "validation"
	case *types.DevshardTx_ValidationVote:
		return "validation_vote"
	case *types.DevshardTx_RevealSeed:
		return "reveal_seed"
	case *types.DevshardTx_FinalizeRound:
		return "finalize_round"
	default:
		return "unknown"
	}
}

func main() {
	if len(os.Args) != 5 {
		fmt.Fprintf(os.Stderr, "usage: p3decode <inferences.ndjson> <diffs.ndjson> <epoch> <out.csv>\n")
		os.Exit(2)
	}

	infPath := os.Args[1]
	diffPath := os.Args[2]
	epoch, err := strconv.Atoi(os.Args[3])
	must(err)
	outPath := os.Args[4]

	escrows := loadEpochEscrows(infPath, epoch)

	in, err := os.Open(diffPath)
	must(err)
	defer in.Close()

	out, err := os.Create(outPath)
	must(err)
	defer out.Close()

	w := csv.NewWriter(out)
	defer w.Flush()
	must(w.Write([]string{
		"epoch", "escrow_id", "nonce", "tx_index", "kind", "inference_id",
		"slot", "valid", "reason", "input_length", "max_tokens",
		"input_tokens", "output_tokens", "started_at", "confirmed_at",
		"model", "escrow_id_field", "vote_count", "accept_count",
	}))

	sc := bufio.NewScanner(in)
	sc.Buffer(make([]byte, 1024), 64*1024*1024)
	rows := 0
	decoded := 0
	for sc.Scan() {
		rows++
		var r DiffRow
		must(json.Unmarshal(sc.Bytes(), &r))
		if !escrows[r.EscrowID] {
			continue
		}

		raw, err := base64.StdEncoding.DecodeString(r.RawTxsB64)
		must(err)
		var diff types.DiffContent
		must(proto.Unmarshal(raw, &diff))
		decoded++

		for i, tx := range diff.Txs {
			rec := []string{
				strconv.Itoa(epoch), strconv.Itoa(r.EscrowID),
				strconv.FormatUint(r.Nonce, 10), strconv.Itoa(i), txKind(tx),
				"", "", "", "", "", "", "", "", "", "", "", "", "", "",
			}

			switch inner := tx.GetTx().(type) {
			case *types.DevshardTx_StartInference:
				m := inner.StartInference
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[9] = strconv.FormatUint(m.InputLength, 10)
				rec[10] = strconv.FormatUint(m.MaxTokens, 10)
				rec[13] = strconv.FormatInt(m.StartedAt, 10)
				rec[15] = m.Model
			case *types.DevshardTx_ConfirmStart:
				m := inner.ConfirmStart
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[14] = strconv.FormatInt(m.ConfirmedAt, 10)
			case *types.DevshardTx_FinishInference:
				m := inner.FinishInference
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[6] = strconv.FormatUint(uint64(m.ExecutorSlot), 10)
				rec[11] = strconv.FormatUint(m.InputTokens, 10)
				rec[12] = strconv.FormatUint(m.OutputTokens, 10)
				rec[16] = m.EscrowId
			case *types.DevshardTx_TimeoutInference:
				m := inner.TimeoutInference
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[8] = m.Reason.String()
				rec[17] = strconv.Itoa(len(m.Votes))
				acc := 0
				for _, v := range m.Votes {
					if v.Accept {
						acc++
					}
				}
				rec[18] = strconv.Itoa(acc)
			case *types.DevshardTx_Validation:
				m := inner.Validation
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[6] = strconv.FormatUint(uint64(m.ValidatorSlot), 10)
				rec[7] = strconv.FormatBool(m.Valid)
				rec[16] = m.EscrowId
			case *types.DevshardTx_ValidationVote:
				m := inner.ValidationVote
				rec[5] = strconv.FormatUint(m.InferenceId, 10)
				rec[6] = strconv.FormatUint(uint64(m.VoterSlot), 10)
				rec[7] = strconv.FormatBool(m.VoteValid)
				rec[16] = m.EscrowId
			case *types.DevshardTx_RevealSeed:
				m := inner.RevealSeed
				rec[6] = strconv.FormatUint(uint64(m.SlotId), 10)
				rec[16] = m.EscrowId
			}
			must(w.Write(rec))
		}
	}
	must(sc.Err())
	fmt.Fprintf(os.Stderr, "rows=%d decoded_diffs=%d epoch_escrows=%d\n", rows, decoded, len(escrows))
}
