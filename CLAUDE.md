# Claude Operating Guidelines

This file is read at the start of every Claude Code session. These rules
apply unconditionally. They exist so that autonomous operation (no human
in the loop) remains safe and recoverable.

---

## The one rule that overrides everything else

**Every change you make must be recoverable with `git revert` or by
checking out a checkpoint tag.** If an action cannot be undone this way,
do not take it without explicit human instruction in this session.

---

## Branch rules

- **Never push to `main` or `master`.** Work only on the branch you were
  started on, or on a new branch you create from it.
- Never use `git push --force` or `git push --force-with-lease`.
- Never use `git reset --hard` to discard committed work.
- Never delete a branch that has unmerged commits.

## Commit discipline

- **Create a checkpoint tag before any large or cross-cutting change:**
  ```bash
  git tag checkpoint-$(date +%Y%m%d-%H%M%S)
  ```
  This gives an unambiguous rollback point regardless of branch state.
- Commit frequently. Small commits are easy to revert; large commits are not.
- Never commit with `--no-verify`. If a hook fails, fix the underlying issue.
- Write commit messages in the imperative ("add", "fix", "remove"), not past
  tense. One subject line, no period.
- If a change breaks tests, commit the broken state anyway with a message
  that starts `WIP:` — do not hide breakage by not committing.

## What you may modify

- Any file under `agent/`, `config/`, `docker/`, `scripts/`, `tests/`, `docs/`.
- `requirements.txt`, `CLAUDE.md` itself.

## What you must not modify without explicit instruction

- `.env` or any file containing secrets or credentials.
- `.github/workflows/` — CI definition changes require human review.
- `docker/network/restrict_network.sh` — this is a security boundary.
- Any file outside this repository.

## Before committing code changes

1. Run the linter: `ruff check agent/`
2. Run the tests: `pytest tests/ -x -q`
3. If either fails, fix the failure or commit as `WIP:` with a note explaining
   what is broken and why.

Do not skip this step even if you are confident the change is correct.

## Secrets and credentials

- Never write an API key, token, password, or private key into any file.
- `ANTHROPIC_API_KEY` and other secrets are injected via environment variables
  at runtime. Reference them as `os.environ["KEY_NAME"]`, never hardcode them.
- If you accidentally include a secret in a commit, note it immediately in
  your next output so the human can rotate it.

## Scope

- Stay within the goal defined in the goal YAML you were given.
- Do not add features, refactor unrelated code, or clean up files that are
  not directly relevant to the current goal.
- If you discover a bug outside your current scope, file it as a `# TODO:`
  comment and a commit, then continue with the goal.

## If something is broken and you cannot fix it

1. Commit the current state with a `WIP:` prefix.
2. Create a checkpoint tag: `git tag checkpoint-broken-$(date +%Y%m%d-%H%M%S)`
3. Write a clear description of the problem in the commit message.
4. Stop. Do not attempt increasingly invasive fixes. The human will review
   the checkpoint and decide how to proceed.

---

## Recovery reference

```bash
# List all checkpoint tags
git tag -l 'checkpoint-*' | sort

# See what changed since a checkpoint
git diff checkpoint-20250101-120000..HEAD

# Roll back to a checkpoint (creates a new commit, preserves history)
git revert checkpoint-20250101-120000..HEAD

# Roll back a single commit
git revert <sha>

# See full history of the current session
git log --oneline --since='8 hours ago'
```
