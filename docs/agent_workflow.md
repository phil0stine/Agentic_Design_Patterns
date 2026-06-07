# Safe Agent Workflow

This document describes how to give the agent access to your stack while
preserving the ability to recover from any mistake it makes.

## Principle

> Git + branch protection + CI is a complete recovery system.
> Every change is tracked, reviewable, and revertable.
> The only question is preventing the agent from bypassing the review gate.

## The workflow

```
  1. Human writes a goal YAML
  2. Human starts the agent with that goal
  3. Agent works on its branch (claude/...)
  4. Agent opens a PR when done
  5. CI runs automatically (lint, tests, docker build, secret scan)
  6. Human reviews the PR diff
  7. Human merges (or closes)
  8. Human separately decides when to update the robot's pinned image
```

The agent never touches `main`. The robot never auto-updates.

## What the agent can safely do

- Create and push to its own branches
- Modify any file in the repository
- Open PRs, respond to review comments, push fixes
- Read logs and CI output

## What requires a human

- Merging any PR into `main`
- Updating the pinned image digest on the robot
- Granting new repository permissions
- Configuring secrets (API keys, registry credentials)

## Giving the agent repo access

Create a GitHub fine-grained personal access token with:

| Permission | Level |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Workflows | Read and write |
| Metadata | Read (required) |
| Administration | **None** |
| Secrets | **None** |

Set `GITHUB_TOKEN` in the agent's environment (via `.env`).
Do **not** give it admin or secret access.

## Connecting the agent to your running stack (read-only telemetry)

For the agent to observe your stack's actual state during development
(not just in SITL/BITL), you can expose a read-only ROS2 bridge:

```bash
# On the robot / dev machine, run a websocket bridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090
```

The agent can subscribe to topics via the bridge without having any write
access to the robot's control plane. Actual commands only go through
the SITL/BITL Docker container where network is restricted.

## Recovery procedures

### Bad code merged to main
```bash
git log --oneline -10          # find the bad merge commit
git revert -m 1 <sha>          # creates a revert commit
git push origin main           # requires admin bypass or another PR
```

### Bad image deployed to robot
```bash
# On the robot — change digest to previous known-good
vim /etc/autonomy/robot.env
docker restart autonomy_agent
```

### Agent committed a secret
```bash
# 1. Rotate the secret immediately (the key is compromised)
# 2. Remove from git history
git filter-repo --path <file> --invert-paths
# 3. Force push (requires admin, coordinate with team)
git push --force origin <branch>
# 4. Open a PR to remove from main if it got there
```

### Agent broke the Docker build
```bash
# CI will block the merge — just close the PR and open a new one
# with a fix, or push a fix commit to the same branch
```
