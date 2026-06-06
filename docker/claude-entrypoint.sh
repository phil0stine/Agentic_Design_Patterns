#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "[entrypoint] ERROR: ANTHROPIC_API_KEY is not set."
    exit 1
fi

if [[ ! -d /workspace/.git ]]; then
    echo "[entrypoint] ERROR: /workspace is not a git repository."
    echo "             Mount your repo: -v /path/to/repo:/workspace"
    exit 1
fi

# Lock down the network before doing anything else.
# After this point the container cannot reach GitHub, npm, PyPI, or
# any host except api.anthropic.com:443.
echo "[entrypoint] Applying network restrictions..."
restrict_network || echo "[entrypoint] WARNING: network restriction failed (missing CAP_NET_ADMIN?)"

# Set up git identity and create the session checkpoint tag.
workspace_init

# Read the goal from a file or from the AGENT_GOAL env var.
if [[ -n "${GOAL_FILE:-}" && -f "${GOAL_FILE}" ]]; then
    PROMPT=$(cat "${GOAL_FILE}")
elif [[ -n "${AGENT_GOAL:-}" ]]; then
    PROMPT="${AGENT_GOAL}"
else
    echo "[entrypoint] ERROR: provide AGENT_GOAL or GOAL_FILE."
    exit 1
fi

echo "[entrypoint] Starting Claude Code agent..."
echo "[entrypoint] Goal: ${PROMPT:0:120}..."
echo ""

# Run Claude Code non-interactively.
# --print: single-shot, no interactive session
# --dangerously-skip-permissions: required for unattended container use;
#   safe here because the network restriction and read-only git remote
#   are the real guardrails, not Claude's own permission prompts.
claude --print "${PROMPT}" \
       --dangerously-skip-permissions
