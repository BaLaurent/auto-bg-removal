#!/usr/bin/env bash
# Télécharge les 4 checkpoints SAM 2.1 de Meta dans backend/checkpoints/.
# Usage : ./scripts/download_checkpoints.sh [tiny|small|base_plus|large|all]

set -euo pipefail

DEST="${MODEL_DIR:-$(dirname "$0")/../backend/checkpoints}"
DEST="$(realpath "$DEST")"
mkdir -p "$DEST"

BASE_URL="https://dl.fbaipublicfiles.com/segment_anything_2/092824"

declare -A FILES=(
  [tiny]="sam2.1_hiera_tiny.pt"
  [small]="sam2.1_hiera_small.pt"
  [base_plus]="sam2.1_hiera_base_plus.pt"
  [large]="sam2.1_hiera_large.pt"
)

download_one() {
  local key="$1"
  local file="${FILES[$key]}"
  local out="$DEST/$file"
  if [[ -f "$out" ]]; then
    echo "✓ $file déjà présent dans $DEST"
    return
  fi
  echo "↓ Téléchargement de $file…"
  curl -L --fail --progress-bar -o "$out.tmp" "$BASE_URL/$file"
  mv "$out.tmp" "$out"
  echo "✓ $file téléchargé"
}

target="${1:-all}"
case "$target" in
  tiny|small|base_plus|large)
    download_one "$target"
    ;;
  all)
    for k in tiny small base_plus large; do download_one "$k"; done
    ;;
  *)
    echo "Usage : $0 [tiny|small|base_plus|large|all]" >&2
    exit 2
    ;;
esac

echo
echo "Checkpoints prêts dans : $DEST"
ls -lh "$DEST"/*.pt 2>/dev/null || true
