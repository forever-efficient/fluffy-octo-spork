#!/usr/bin/env bash
# Lightweight Docker cleanup for macOS/Docker Desktop
# - Frees space from build cache and unused images
# - Optional: prune stopped containers/networks and unused volumes
# Safe defaults: does NOT remove volumes or containers unless flagged

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: docker-prune-macos.sh [options]

Options:
  -n    Dry run (show what will run, don't execute)
  -a    Aggressive prune: also remove stopped containers and unused networks (docker system prune -f)
  -v    Prune unused volumes (WARNING: deletes any volumes not used by a container)
  -h    Show this help

Examples:
  # Safe defaults: prune build cache + unused images
  ./docker-prune-macos.sh

  # Also remove stopped containers/networks
  ./docker-prune-macos.sh -a

  # Also prune unused volumes (careful)
  ./docker-prune-macos.sh -v

  # Combine flags
  ./docker-prune-macos.sh -a -v
EOF
}

DRY_RUN=0
AGGRESSIVE=0
VOLUMES=0
while getopts ":navh" opt; do
  case "$opt" in
    n) DRY_RUN=1 ;;
    a) AGGRESSIVE=1 ;;
    v) VOLUMES=1 ;;
    h) usage; exit 0 ;;
    :) echo "Option -$OPTARG requires an argument"; usage; exit 2 ;;
    \?) echo "Unknown option: -$OPTARG"; usage; exit 2 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker CLI not found. Install Docker Desktop for Mac." >&2
  exit 1
fi

run() {
  echo "+ $*"
  if [ "$DRY_RUN" -eq 0 ]; then
    eval "$@"
  fi
}

echo "[1/4] Current disk usage:"
run docker system df || true

echo "\n[2/4] Pruning build cache (aggressive)..."
run docker builder prune -af || true

# If buildx exists, prune there too (some caches are separate)
if command -v docker >/dev/null 2>&1 && docker buildx version >/dev/null 2>&1; then
  echo "\n[2b/4] Pruning buildx cache (aggressive)..."
  run docker buildx prune -af || true
fi

echo "\n[3/4] Removing unused images..."
run docker image prune -af || true

if [ "$AGGRESSIVE" -eq 1 ]; then
  echo "\n[3b/4] Aggressive prune: removing stopped containers and unused networks..."
  run docker system prune -f || true
fi

if [ "$VOLUMES" -eq 1 ]; then
  echo "\n[3c/4] Pruning unused volumes (WARNING: irreversible)..."
  run docker volume prune -f || true
fi

echo "\n[4/4] Disk usage after cleanup:"
run docker system df || true

echo "\nDone."
