#!/usr/bin/env bash
# Re-run the smoke from scratch: ticket 29, seeded, 1 rep per arm, then grading and summary.
# usage: smoke.sh <raw-folder>      (the folder must not already hold reviews.jsonl)
set -euo pipefail
RAW="${1:?usage: smoke.sh <raw-folder>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$RAW"
[ -e "$RAW/reviews.jsonl" ] && { echo "refusing: $RAW/reviews.jsonl exists" >&2; exit 1; }
python3 "$HERE/prep.py" 29 seeded >/dev/null
python3 "$HERE/run_reviews.py" --raw "$RAW" --tickets 29 --conditions seeded --reps 1 --seed 1
python3 "$HERE/grade.py" --raw "$RAW" --seed 1
python3 "$HERE/summary.py" --raw "$RAW" | tee "$RAW/summary.json"
