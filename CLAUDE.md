# Claude Operating Guidelines

This file is read at the start of every Claude Code session. These rules
apply unconditionally and exist so that autonomous operation (no human
in the loop) remains safe and recoverable.

---

## The one rule that overrides everything else

**Every change you make must be recoverable with `git revert` or by
checking out a checkpoint tag.** If an action cannot be undone this way,
do not take it without explicit human instruction in this session.

---

## Network and push isolation

You are running inside a container where:
- The only reachable external host is `api.anthropic.com:443`
- `github.com` and `api.github.com` are unreachable at the network layer
- `git push` will fail — this is intentional and enforced by firewall rules,
  not just a policy

**Do not attempt `git push`, `git fetch`, `git pull`, or `git remote`.**
They will time out. The human will push after reviewing your commits.

Your job is to commit clean, well-tested changes to the local branch.
The human decides when and whether to push them.

---

## Branch rules

- Work only on the branch that was checked out when the container started.
- Do not create branches named `main` or `master`.
- Never use `git reset --hard` to discard committed work.

## Commit discipline

- **Create a checkpoint tag before any large or cross-cutting change:**
  ```bash
  git tag checkpoint-$(date +%Y%m%d-%H%M%S)
  ```
- Commit frequently. Small commits are easy to revert; large commits are not.
- Never commit with `--no-verify`. If a hook fails, fix the underlying issue.
- If a change breaks tests, commit the broken state anyway with a message
  that starts `WIP:` — do not hide breakage.

## Before committing code changes

1. Run the linter: `ruff check agent/`
2. Run the tests: `pytest tests/ -x -q`
3. If either fails, fix the failure or commit as `WIP:` with a note.

## What you may modify

- Any file under `agent/`, `config/`, `docker/`, `scripts/`, `tests/`, `docs/`.
- `requirements.txt`, `CLAUDE.md` itself.

## What you must not modify

- `.env` or any file containing secrets or credentials.
- `.github/workflows/` — CI changes require human review.
- `docker/network/restrict_claude.sh` — this is the security boundary.

## Secrets

- Never write an API key, token, password, or private key into any file.
- If you accidentally include a secret in a commit, note it prominently
  so the human can rotate it before pushing.

## Scope

- Stay within the goal you were given.
- Do not refactor unrelated code or clean up files outside the goal's scope.
- If you find a bug outside scope, leave a `# TODO:` comment and continue.

## If something is broken and you cannot fix it

1. Commit the current state with `WIP:` prefix.
2. Create a checkpoint tag: `git tag checkpoint-stuck-$(date +%Y%m%d-%H%M%S)`
3. Explain the problem clearly in the commit message.
4. Stop. The human will review.

---

## Recovery reference (for the human, after the session)

```bash
# Review what the agent did
bash scripts/review_and_push.sh

# Roll back everything since the session checkpoint
bash scripts/rollback.sh

# Roll back a specific commit
git revert <sha>

# See all checkpoint tags
git tag -l 'checkpoint-*' | sort
```
