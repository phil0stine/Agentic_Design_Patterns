#!/usr/bin/env bash
set -euo pipefail

# Source ROS2 base
source /opt/ros/jazzy/setup.bash

# Source user workspace if mounted
if [[ -f /workspace/install/setup.bash ]]; then
    source /workspace/install/setup.bash
fi

# Validate API key before anything else
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "[entrypoint] ERROR: ANTHROPIC_API_KEY is not set. Exiting."
    exit 1
fi

# Apply network restrictions (requires CAP_NET_ADMIN)
if [[ "${RESTRICT_NETWORK:-true}" == "true" ]]; then
    echo "[entrypoint] Applying network restrictions..."
    /app/docker/network/restrict_network.sh || \
        echo "[entrypoint] WARNING: Network restriction failed (missing CAP_NET_ADMIN?)"
else
    echo "[entrypoint] WARNING: RESTRICT_NETWORK=false — skipping network lockdown."
fi

exec "$@"
