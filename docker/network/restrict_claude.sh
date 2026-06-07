#!/usr/bin/env bash
# Network restriction for the Claude Code container.
# Allows ONLY: loopback + DNS + api.anthropic.com:443
# Blocks:      GitHub, npm, PyPI, and everything else.
# Requires CAP_NET_ADMIN.
set -euo pipefail

ANTHROPIC_HOST="api.anthropic.com"

echo "[network] Resolving ${ANTHROPIC_HOST}..."
ANTHROPIC_IPS=$(getent ahosts "${ANTHROPIC_HOST}" 2>/dev/null \
    | awk '{print $1}' | sort -u || true)

if [[ -z "${ANTHROPIC_IPS}" ]]; then
    echo "[network] ERROR: cannot resolve ${ANTHROPIC_HOST} before lockdown."
    echo "[network]        Ensure DNS is reachable at container start."
    exit 1
fi

echo "[network] Resolved ${ANTHROPIC_HOST} -> ${ANTHROPIC_IPS}"

# Flush
iptables -F OUTPUT 2>/dev/null || true
iptables -F INPUT  2>/dev/null || true

# Loopback
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A INPUT  -i lo -j ACCEPT

# Established / related
iptables -A INPUT  -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# DNS — needed only until we have the IPs; kept open because Anthropic
# may return multiple addresses and we want re-resolution to work.
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# api.anthropic.com:443 only
for ip in ${ANTHROPIC_IPS}; do
    echo "[network] Allowing ${ip}:443"
    iptables -A OUTPUT -p tcp -d "${ip}" --dport 443 -j ACCEPT
done

# Drop everything else — including github.com, api.github.com,
# registry.npmjs.org, pypi.org, and any other egress.
iptables -A OUTPUT -j DROP

echo "[network] Locked. Only api.anthropic.com:443 + loopback reachable."
echo "[network] git push will fail (GitHub is unreachable by design)."
