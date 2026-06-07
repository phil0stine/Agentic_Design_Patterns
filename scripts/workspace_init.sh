#!/usr/bin/env bash
# Run once at container start, before the agent begins work.
# Sets up the git workspace so every session starts from a known-good state
# and leaves a checkpoint tag that always works as a rollback point.
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspace}"
cd "${REPO_ROOT}"

# ---- 1. Confirm we are NOT on a protected branch --------------------
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "${CURRENT_BRANCH}" == "main" || "${CURRENT_BRANCH}" == "master" ]]; then
    echo "ERROR: workspace_init: refusing to start on protected branch '${CURRENT_BRANCH}'."
    echo "       Check out a feature branch before starting the agent."
    exit 1
fi
echo "[init] Branch: ${CURRENT_BRANCH}"

# ---- 2. Ensure working tree is clean (commit or stash first) --------
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "[init] Uncommitted changes detected — creating a WIP commit."
    git add -A
    git commit -m "WIP: uncommitted changes at session start (auto-commit by workspace_init)"
fi

# ---- 3. Record the starting SHA (written to a file the agent can read) --
START_SHA=$(git rev-parse HEAD)
echo "${START_SHA}" > /tmp/agent_session_start_sha
echo "[init] Starting SHA: ${START_SHA}"

# ---- 4. Create a checkpoint tag for this session --------------------
CHECKPOINT="checkpoint-$(date +%Y%m%d-%H%M%S)"
git tag "${CHECKPOINT}"
echo "${CHECKPOINT}" > /tmp/agent_session_checkpoint_tag
echo "[init] Checkpoint tag: ${CHECKPOINT}"

# ---- 5. Configure git identity for commits made inside container ----
git config --local user.name  "${GIT_AUTHOR_NAME:-Autonomy Agent}"
git config --local user.email "${GIT_AUTHOR_EMAIL:-agent@autonomy.local}"

# ---- 6. Print rollback instructions (captured in container logs) ----
cat <<EOF

[init] Workspace ready.
       Branch:      ${CURRENT_BRANCH}
       Start SHA:   ${START_SHA}
       Checkpoint:  ${CHECKPOINT}

       To roll back everything this session does:
         git revert ${CHECKPOINT}..HEAD   # creates revert commits
         # or
         git diff ${CHECKPOINT}..HEAD     # review first

EOF
