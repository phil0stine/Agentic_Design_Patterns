# Branch Protection Setup

Configure these rules on `main` (and `master` if you use it) in
**GitHub → Settings → Branches → Add branch ruleset**.

## Required rules

| Rule | Setting | Why |
|---|---|---|
| Require a pull request before merging | ✅ enabled | Agent cannot push directly to main |
| Required approvals | **1** (minimum) | A human must review every PR |
| Dismiss stale reviews on new commits | ✅ enabled | Re-review required after any push to the PR |
| Require status checks to pass | ✅ enabled | CI must be green before merge is possible |
| Required status checks | `lint`, `validate-config`, `unit-tests`, `docker-build`, `secret-scan` | All five CI jobs |
| Require branches to be up to date | ✅ enabled | No merging stale branches |
| Do not allow bypassing the above settings | ✅ enabled | Applies to admins too |
| Restrict deletions | ✅ enabled | Cannot delete main |
| Block force pushes | ✅ enabled | History is immutable |

## What this means for the agent

The agent (Claude) can:
- Create branches
- Push commits to its own branch
- Open PRs
- Respond to review comments

The agent cannot:
- Push to `main` directly
- Merge its own PRs
- Force-push
- Delete protected branches

A human must click **Merge** for any change to reach the deployed stack.

## Recovery from any bad commit

Because every change goes through a PR:

```bash
# Revert a merged PR (creates a new revert commit, preserves history)
git revert -m 1 <merge-commit-sha>
git push origin main

# Or revert a range of commits
git revert <oldest-sha>^..<newest-sha>
```

There is no state in this repository that cannot be recovered from with a revert.
