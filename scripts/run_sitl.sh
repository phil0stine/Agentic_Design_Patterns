#!/usr/bin/env bash
# Run the autonomy agent in SITL mode.
# Prerequisite: simulator must already be publishing ROS2 topics.
# Usage: bash scripts/run_sitl.sh [goal_yaml]
set -euo pipefail

GOAL_FILE="${1:-config/goals/example_sitl_goal.yaml}"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or export it."
    exit 1
fi

export GOAL_FILE

docker compose \
    -f docker/docker-compose.sitl.yml \
    --env-file .env \
    up --abort-on-container-exit
