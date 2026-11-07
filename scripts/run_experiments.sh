#!/usr/bin/env bash

set -e

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG_LIST="${1:?Usage: $0 <config_list.txt>}"
PROJECT_DIR="${2:?Usage: $0 <config_list.txt> <project_dir>}"

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

while IFS= read -r config || [[ -n "$config" ]]; do
    [[ -z "$config" || "$config" =~ ^[[:space:]]*# ]] && continue

    config_path="$PROJECT_DIR/config/$(basename "$config")"

    echo "Running: $config_path"

    uv run -m edgepii.experiment --config "$config_path"

done < "$CONFIG_LIST"