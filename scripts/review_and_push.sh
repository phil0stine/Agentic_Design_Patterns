#!/usr/bin/env bash
# Review commits made by the agent, then optionally push.
# Run this on the HOST after the Claude Code container exits.
#
# Usage:
#   cd /path/to/repo && bash scripts/review_and_push.sh
#   bash scripts/review_and_push.sh /path/to/repo
set -euo pipefail

REPO="${1:-$(pwd)}"
cd "${REPO}"

if [[ ! -d .git ]]; then
    echo "ERROR: not a git repository: ${REPO}"
    exit 1
fi

# Find the most recent session checkpoint tag
CHECKPOINT=$(git tag -l 'checkpoint-*' | sort | tail -1)
if [[ -z "${CHECKPOINT}" ]]; then
    echo "No checkpoint tag found. Has the agent run yet?"
    exit 1
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_COUNT=$(git rev-list --count "${CHECKPOINT}"..HEAD)

echo "=================================================="
echo "  Agent session review"
echo "  Branch:      ${BRANCH}"
echo "  Checkpoint:  ${CHECKPOINT}"
echo "  New commits: ${COMMIT_COUNT}"
echo "=================================================="
echo ""

if [[ "${COMMIT_COUNT}" -eq 0 ]]; then
    echo "No commits since checkpoint. Nothing to review."
    exit 0
fi

# Show commit log
echo "--- Commits ---"
git log --oneline "${CHECKPOINT}"..HEAD
echo ""

# Show full diff (pipe to pager if large)
echo "--- Diff ---"
LINES=$(git diff "${CHECKPOINT}"..HEAD | wc -l)
if [[ "${LINES}" -gt 200 ]]; then
    echo "(Diff is ${LINES} lines. Showing in pager — press q to exit.)"
    git diff "${CHECKPOINT}"..HEAD | "${PAGER:-less}"
else
    git diff "${CHECKPOINT}"..HEAD
fi
echo ""

# Run tests before offering to push
echo "--- Running tests ---"
if pytest tests/ -q 2>&1; then
    TEST_STATUS="PASSED"
else
    TEST_STATUS="FAILED"
fi
echo "Tests: ${TEST_STATUS}"
echo ""

# Decision
if [[ "${TEST_STATUS}" == "FAILED" ]]; then
    echo "WARNING: tests are failing. Push anyway? [y/N]"
else
    echo "Push ${COMMIT_COUNT} commit(s) to origin/${BRANCH}? [y/N]"
fi

read -rp "> " CONFIRM
if [[ "${CONFIRM}" == "y" || "${CONFIRM}" == "Y" ]]; then
    git push origin "${BRANCH}"
    echo "Pushed. Open a PR at:"
    echo "  https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//;s/\.git$//')/compare/${BRANCH}"
else
    echo "Not pushed. To roll back all agent changes:"
    echo "  bash scripts/rollback.sh ${CHECKPOINT}"
    echo "To push later:"
    echo "  git push origin ${BRANCH}"
fi
