#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Alpaca bot: persist logs/ and data/bars/ on a block volume (DigitalOcean-style).
#
# Prereqs:
#   - Volume mounted on the host (example): /mnt/volume_nyc3_01/alpaca_bot_active/
#   - stock-bot repo checked out at REPO_ROOT (default: directory containing this script/../../)
#
# This script DOES NOT format or mount the volume — only creates dirs and symlinks.
# Run once per droplet after attach/mount, or after a fresh clone. Do not run twice
# if logs/ or data/bars/ already exist as real directories with data you need; move
# data into the volume first, then replace with symlinks.
#
# Usage:
#   export ALPACA_VOLUME_ROOT=/mnt/volume_nyc3_01/alpaca_bot_active
#   bash scripts/ops/mount_alpaca_telemetry_to_volume.sh
# -----------------------------------------------------------------------------

set -euo pipefail

ALPACA_VOLUME_ROOT="${ALPACA_VOLUME_ROOT:-/mnt/volume_nyc3_01/alpaca_bot_active}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ ! -d "${ALPACA_VOLUME_ROOT}" ]]; then
  echo "error: ALPACA_VOLUME_ROOT is not a directory: ${ALPACA_VOLUME_ROOT}" >&2
  echo "  Mount the volume first, then set ALPACA_VOLUME_ROOT to the mount path." >&2
  exit 1
fi

VOL_LOGS="${ALPACA_VOLUME_ROOT}/logs"
VOL_BARS="${ALPACA_VOLUME_ROOT}/data/bars"
DEST_LOGS="${REPO_ROOT}/logs"
DEST_BARS="${REPO_ROOT}/data/bars"

mkdir -p "${VOL_LOGS}" "${VOL_BARS}" "${REPO_ROOT}/data"

# Replace repo logs/ with symlink to volume (backup existing non-symlink dir)
if [[ -e "${DEST_LOGS}" ]] && [[ ! -L "${DEST_LOGS}" ]]; then
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  echo "warning: ${DEST_LOGS} exists; moving to ${DEST_LOGS}.pre_volume.${TS}"
  mv "${DEST_LOGS}" "${DEST_LOGS}.pre_volume.${TS}"
fi
if [[ ! -e "${DEST_LOGS}" ]]; then
  ln -s "${VOL_LOGS}" "${DEST_LOGS}"
  echo "linked ${DEST_LOGS} -> ${VOL_LOGS}"
elif [[ -L "${DEST_LOGS}" ]]; then
  echo "ok: ${DEST_LOGS} already a symlink"
else
  echo "error: could not create symlink at ${DEST_LOGS}" >&2
  exit 1
fi

# Replace repo data/bars/ with symlink
if [[ -e "${DEST_BARS}" ]] && [[ ! -L "${DEST_BARS}" ]]; then
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  echo "warning: ${DEST_BARS} exists; moving to ${DEST_BARS}.pre_volume.${TS}"
  mv "${DEST_BARS}" "${DEST_BARS}.pre_volume.${TS}"
fi
if [[ ! -e "${DEST_BARS}" ]]; then
  ln -s "${VOL_BARS}" "${DEST_BARS}"
  echo "linked ${DEST_BARS} -> ${VOL_BARS}"
elif [[ -L "${DEST_BARS}" ]]; then
  echo "ok: ${DEST_BARS} already a symlink"
else
  echo "error: could not create symlink at ${DEST_BARS}" >&2
  exit 1
fi

echo "done. Volume dirs:"
echo "  logs: ${VOL_LOGS}"
echo "  bars: ${VOL_BARS}"
