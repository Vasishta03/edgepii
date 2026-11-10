#!/usr/bin/env bash

set -e

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG_LIST="${1:?Usage: $0 <config_list.txt>}"
PROJECT_DIR="${2:?Usage: $0 <config_list.txt> <project_dir>}"

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

while IFS= read -r config || [[ -n "$config" ]]; do
    [[ -z "$config" || "$config" =~ ^[[:space:]]*# ]] && continue

    config = "$(basename "$config")"

    echo "Running: $config"

    uv run -m edgepii.benchmark --run "$config" --dataset capid --split test
    uv run -m edgepii.benchmark --run "$config" --dataset capid --split reddit
    uv run -m edgepii.benchmark --run "$config" --dataset capid --split validation
    uv run -m edgepii.benchmark --run "$config" --dataset ai4privacy --split test
    uv run -m edgepii.benchmark --run "$config" --dataset ai4privacy --split validation

done < "$CONFIG_LIST"