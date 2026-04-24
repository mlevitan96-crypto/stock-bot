#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — SHADOW SIGNAL WEIGHTING INITIATION
#
# BOARD-APPROVED PATH:
#   Continuous alpha weighting + shadow replay lab
#
# SCOPE:
#   Shadow-only, read-only, no live/paper impact
#
# PURPOSE:
#   1. Inventory and classify signal gates
#   2. Convert alpha gates to weighted contributors (shadow)
#   3. Define canonical signal schema
#   4. Stand up shadow replay harness
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow reports/board reports/audit shadow/config shadow/replay

echo "=== PHASE 0: ASSERT BOARD APPROVAL ==="
test -f reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md || {
  echo "ERROR: Board decision file missing"
  exit 1
}

grep -q "APPROVE" reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md || {
  echo "ERROR: Board decision not APPROVED"
  exit 1
}

echo "=== PHASE 1: INVENTORY SIGNAL GATES ==="
python3 scripts/shadow/inventory_signal_gates.py \
  --config-dir config \
  --output reports/shadow/SIGNAL_GATE_INVENTORY_${DATE}.json

echo "=== PHASE 2: CLASSIFY GATES (ALPHA vs SAFETY) ==="
python3 scripts/shadow/classify_signal_gates.py \
  --inventory reports/shadow/SIGNAL_GATE_INVENTORY_${DATE}.json \
  --output reports/shadow/SIGNAL_GATE_CLASSIFICATION_${DATE}.json

echo "=== PHASE 3: DEFINE CANONICAL SIGNAL SCHEMA ==="
python3 scripts/shadow/define_signal_schema.py \
  --classification reports/shadow/SIGNAL_GATE_CLASSIFICATION_${DATE}.json \
  --output shadow/config/CANONICAL_SIGNAL_SCHEMA.json

echo "=== PHASE 4: CONVERT ALPHA GATES TO WEIGHTED CONTRIBUTORS (SHADOW) ==="
python3 scripts/shadow/convert_alpha_gates_to_weights.py \
  --schema shadow/config/CANONICAL_SIGNAL_SCHEMA.json \
  --mode shadow \
  --output shadow/config/WEIGHTED_SIGNAL_MODEL.json

echo "=== PHASE 5: INITIALIZE SHADOW REPLAY HARNESS ==="
python3 scripts/shadow/init_shadow_replay_harness.py \
  --ledger-dir reports/ledger \
  --signal-model shadow/config/WEIGHTED_SIGNAL_MODEL.json \
  --read-only \
  --output reports/shadow/SHADOW_REPLAY_READY_${DATE}.json

echo "=== SHADOW SIGNAL WEIGHTING FOUNDATION COMPLETE ==="
