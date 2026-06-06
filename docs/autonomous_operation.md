# Autonomous Operation Safety Model

## What makes changes recoverable

Git is the safety system. Every change the agent makes is a commit.
Every commit is revertable. The only truly unrecoverable git operations
are those that destroy history (force push, filter-repo, reset --hard
on pushed commits) — CLAUDE.md prohibits these, and the GitHub token
does not have permission to force-push to protected branches.

```
Worst case: agent makes 50 bad commits across 10 files
Recovery:   git revert <checkpoint>..HEAD
Time:       30 seconds
Data lost:  none
```

## The three-layer safety model

```
┌────────────────────────────────────────────┐
│  Layer 1: CLAUDE.md (behavioral)               │
│  Claude reads this at startup and follows it.  │
│  Covers: branch rules, commit discipline,      │
│  what files are off-limits, secret handling.   │
└────────────────────────────────────────────┘
         If Claude ignores CLAUDE.md:
┌────────────────────────────────────────────┐
│  Layer 2: GitHub token permissions             │
│  Fine-grained token: Contents + PRs only.     │
│  No admin. Cannot force-push. Cannot delete   │
│  protected branches. Cannot modify secrets.   │
└────────────────────────────────────────────┘
         If the token is somehow misused:
┌────────────────────────────────────────────┐
│  Layer 3: Checkpoint tags + git revert        │
│  workspace_init.sh tags HEAD at session start. │
│  Any state between then and now is revertable  │
│  in a single command.                          │
└────────────────────────────────────────────┘
```

## Container startup sequence

```bash
# 1. workspace_init.sh runs before the agent
bash /workspace/scripts/workspace_init.sh
# └─ confirms not on main
# └─ commits any leftover changes
# └─ records start SHA to /tmp/agent_session_start_sha
# └─ creates checkpoint-YYYYMMDD-HHMMSS tag
# └─ sets git identity

# 2. Agent runs (claude --no-interactive or similar)
# 3. All changes are committed to the feature branch
# 4. Human reviews the diff and merges (or reverts)
```

## GitHub token setup

Create a **fine-grained personal access token** at
GitHub → Settings → Developer Settings → Fine-grained tokens:

| Permission | Level | Reason |
|---|---|---|
| Contents | Read and write | Push commits |
| Pull requests | Read and write | Open PRs |
| Workflows | Read | Read CI status |
| Metadata | Read | Required |
| Administration | **None** | Cannot touch branch protection |
| Secrets | **None** | Cannot read or write secrets |

Set in the container:
```bash
export GITHUB_TOKEN=github_pat_...
git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/org/repo.git
```

## What is genuinely unrecoverable

Very little, when the above is in place:

| Action | Recoverable? | Prevention |
|---|---|---|
| Bad commits on feature branch | Yes — `git revert` | Checkpoint tag |
| Merging a bad PR to main | Yes — `git revert -m 1 <sha>` | Human merge gate |
| Committing a secret | Token must be rotated (not git-recoverable) | CLAUDE.md rule + secret scan CI |
| Force-pushing main | Yes if you have a backup; hard otherwise | Token has no force-push permission |
| Deleting a protected branch | Not possible | Branch protection |
| Corrupting local files | Yes — `git checkout <checkpoint>` | Checkpoint tag |

The only genuinely bad outcome is **a secret leaking into a commit**.
That requires rotating the credential. The CLAUDE.md rule and the CI
secret scan are the defenses against it.

## Running the agent autonomously

```bash
# In the Claude Code container:
bash /workspace/scripts/workspace_init.sh

# Run Claude Code non-interactively with your goal
claude --print "$(cat /active_goal.yaml)" \
       --allowedTools Edit,Write,Bash,Read,Glob,Grep

# After the session, review what changed
git log --oneline checkpoint-$(cat /tmp/agent_session_checkpoint_tag | cut -d- -f2-)..HEAD
git diff checkpoint-$(cat /tmp/agent_session_checkpoint_tag | cut -d- -f2-)..HEAD
```
