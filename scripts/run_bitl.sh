#!/usr/bin/env bash
# Run the autonomy agent in BITL mode against a ROS2 bag.
# Usage: bash scripts/run_bitl.sh <bag_dir> [bag_file] [goal_yaml]
set -euo pipefail

BAG_PATH="${1:-}"
BAG_FILE="${2:-bag}"
GOAL_FILE="${3:-config/goals/example_bitl_goal.yaml}"

if [[ -z "${BAG_PATH}" ]]; then
    echo "Usage: $0 <absolute_path_to_bag_dir> [bag_filename] [goal_yaml]"
    exit 1
fi

if [[ ! -d "${BAG_PATH}" ]]; then
    echo "ERROR: BAG_PATH does not exist: ${BAG_PATH}"
    exit 1
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or export it."
    exit 1
fi

export BAG_PATH BAG_FILE GOAL_FILE

docker compose \
    -f docker/docker-compose.bitl.yml \
    --env-file .env \
    up --abort-on-container-exit
