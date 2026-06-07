# Deployment Pinning

The running robot must never be affected by code changes in a branch or by
pulling `latest`. Pin deployments to an immutable image digest.

## The model

```
  Developer / Agent
       │
       │  git push → PR → CI → human review → merge to main
       │
  main branch
       │
       │  CI on main builds + pushes image tagged with git SHA
       │
  Container registry
       │  ghcr.io/yourorg/autonomy-stack:sha-abc1234
       │  ghcr.io/yourorg/autonomy-stack:sha-abc1234@sha256:...
       │
  Robot deployment (pinned digest)
       │  ONLY updated by explicit human action
       ▼
  Running stack
```

A broken branch, a bad commit, or a misbehaving agent **cannot reach the
running robot** unless a human explicitly updates the pinned digest.

## How to pin

### 1. Tag images by git SHA in CI

Add this to `.github/workflows/ci.yml` (runs on `main` push only):

```yaml
- name: Push image on main
  if: github.ref == 'refs/heads/main'
  uses: docker/build-push-action@v5
  with:
    context: .
    file: docker/Dockerfile.x86
    push: true
    tags: |
      ghcr.io/${{ github.repository_owner }}/autonomy-stack:sha-${{ github.sha }}
      ghcr.io/${{ github.repository_owner }}/autonomy-stack:latest
    # 'latest' is updated but the robot never uses it
```

### 2. Get the immutable digest after push

```bash
docker pull ghcr.io/yourorg/autonomy-stack:sha-abc1234
docker inspect ghcr.io/yourorg/autonomy-stack:sha-abc1234 \
  --format '{{index .RepoDigests 0}}'
# ghcr.io/yourorg/autonomy-stack@sha256:deadbeef...
```

### 3. Deploy the robot using the digest, never a tag

In your robot's deploy config (e.g. an `.env` file on the robot):

```bash
AUTONOMY_IMAGE=ghcr.io/yourorg/autonomy-stack@sha256:deadbeef...
```

```bash
# On the robot:
docker pull "${AUTONOMY_IMAGE}"
docker run --rm \
  --env-file /etc/autonomy/robot.env \
  --network host \
  --cap-add NET_ADMIN \
  "${AUTONOMY_IMAGE}" \
  python3 -m agent.main --mode sitl --goal /active_goal.yaml
```

To update the robot to a new version:

```bash
# Human action required — update the digest in robot.env
vim /etc/autonomy/robot.env   # change the sha256 digest
# restart the container
```

### 4. Rollback

Rollback = change the digest back to the previous known-good value:

```bash
# On the robot:
AUTONOMY_IMAGE=ghcr.io/yourorg/autonomy-stack@sha256:<previous-digest>
```

No git operations required. The container registry retains all pushed images.

## Summary

| Layer | Protection |
|---|---|
| Branch protection | Agent can't touch main |
| CI status checks | Broken code can't merge |
| Human review required | Human signs off before merge |
| SHA-pinned image | Running robot unaffected by repo changes |
| Digest (not tag) | Even `sha-abc` tags are mutable; digest is not |
| `git revert` | Every merged change is recoverable in one command |
