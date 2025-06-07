#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 [qr-code.png|'-' for stdin] [--out=filename] [--pubkey-to-stdout]" >&2
  exit 1
fi

input=""
outfile=""
pubkey_to_stdout=0

# Parse arguments
for arg in "$@"; do
  case "$arg" in
    --out=*)
      outfile="${arg#--out=}"
      ;;
    --pubkey-to-stdout)
      pubkey_to_stdout=1
      ;;
    -*)
      input="$arg"
      ;;
    *)
      input="$arg"
      ;;
  esac
done

# Decode JSON from PNG or stdin
if [[ "$input" == "-" || -z "$input" ]]; then
  json=$(cat)
else
  if ! command -v zbarimg &>/dev/null; then
    echo "❌ zbarimg not found. Please install it." >&2
    exit 1
  fi
  json=$(zbarimg --quiet --raw "$input")
fi

# Build command
cmd=(./reconstruct-keys.py -)
[[ -n "$outfile" ]] && cmd+=("$outfile")
[[ "$pubkey_to_stdout" -eq 1 ]] && cmd+=(--pubkey-to-stdout)

# Run it
echo "$json" | "${cmd[@]}"

