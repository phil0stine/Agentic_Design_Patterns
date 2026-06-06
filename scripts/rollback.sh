#!/usr/bin/env bash
# Roll back all changes made since the last session checkpoint.
# Creates revert commits (non-destructive — history is preserved).
# Usage:
#   bash scripts/rollback.sh                    # roll back to last checkpoint
#   bash scripts/rollback.sh checkpoint-20250101-120000  # roll back to specific tag
set -euo pipefail

if [[ -n "${1:-}" ]]; then
    CHECKPOINT="$1"
elif [[ -f /tmp/agent_session_checkpoint_tag ]]; then
    CHECKPOINT=$(cat /tmp/agent_session_checkpoint_tag)
else
    echo "Usage: $0 [checkpoint-tag]"
    echo "Available checkpoints:"
    git tag -l 'checkpoint-*' | sort
    exit 1
fi

echo "Rolling back to: ${CHECKPOINT}"
echo "Commits to revert:"
git log --oneline "${CHECKPOINT}"..HEAD
echo ""

read -rp "Proceed? [y/N] " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

# Revert from HEAD back to checkpoint (newest first)
git revert --no-edit "${CHECKPOINT}"..HEAD
echo "Done. All changes since ${CHECKPOINT} have been reverted."
echo "Push with: git push origin $(git rev-parse --abbrev-ref HEAD)"
