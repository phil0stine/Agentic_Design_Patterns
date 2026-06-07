#!/usr/bin/env bash
# Start the air-gapped Claude Code agent against your local repo.
# The agent can commit but cannot push. Review with review_and_push.sh.
#
# Usage:
#   bash scripts/run_claude_agent.sh <path-to-repo> <"goal string" or @goal-file>
#
# Examples:
#   bash scripts/run_claude_agent.sh ~/my_stack "Add lidar dropout detection to the perception pipeline"
#   bash scripts/run_claude_agent.sh ~/my_stack @goals/fix_nav_timeout.txt
set -euo pipefail

WORKSPACE_PATH="${1:-}"
GOAL_INPUT="${2:-}"

if [[ -z "${WORKSPACE_PATH}" || -z "${GOAL_INPUT}" ]]; then
    echo "Usage: $0 <repo-path> <\"goal\" or @/path/to/goal-file.txt>"
    exit 1
fi

if [[ ! -d "${WORKSPACE_PATH}/.git" ]]; then
    echo "ERROR: ${WORKSPACE_PATH} is not a git repository."
    exit 1
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set."
    exit 1
fi

# Resolve goal: inline string or file reference (@/path/to/file)
if [[ "${GOAL_INPUT}" == @* ]]; then
    GOAL_FILE_PATH="${GOAL_INPUT#@}"
    if [[ ! -f "${GOAL_FILE_PATH}" ]]; then
        echo "ERROR: goal file not found: ${GOAL_FILE_PATH}"
        exit 1
    fi
    export GOAL_FILE="${GOAL_FILE_PATH}"
    export AGENT_GOAL=""
else
    export AGENT_GOAL="${GOAL_INPUT}"
    export GOAL_FILE=""
fi

export WORKSPACE_PATH

echo "=================================================="
echo "  Claude Code Agent (air-gapped)"
echo "  Repo:   ${WORKSPACE_PATH}"
echo "  Goal:   ${AGENT_GOAL:-$(cat "${GOAL_FILE}")}"
echo "  Network: api.anthropic.com:443 only"
echo "  Push:   BLOCKED inside container"
echo "=================================================="
echo ""

docker compose \
    -f "$(dirname "$0")/../docker/docker-compose.claude-code.yml" \
    --env-file "$(dirname "$0")/../.env" \
    up --abort-on-container-exit

echo ""
echo "Agent session complete."
echo "Review commits with:"
echo "  cd ${WORKSPACE_PATH} && bash scripts/review_and_push.sh"
