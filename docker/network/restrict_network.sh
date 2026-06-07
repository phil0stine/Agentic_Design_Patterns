#!/usr/bin/env bash
# Restrict container egress to api.anthropic.com (HTTPS) + ROS2 DDS + loopback.
# Requires CAP_NET_ADMIN. Called by entrypoint.sh.
set -euo pipefail

ANTHROPIC_HOST="api.anthropic.com"
ROS_SUBNET="${ROS_NETWORK_SUBNET:-127.0.0.0/8}"

echo "[network] Resolving ${ANTHROPIC_HOST}..."
ANTHROPIC_IPS=$(getent ahosts "${ANTHROPIC_HOST}" 2>/dev/null \
    | awk '{print $1}' | sort -u || true)

if [[ -z "${ANTHROPIC_IPS}" ]]; then
    echo "[network] WARNING: Could not resolve ${ANTHROPIC_HOST}. "
    echo "[network]          Ensure DNS is reachable before restriction is applied."
fi

echo "[network] Flushing existing rules..."
iptables -F OUTPUT 2>/dev/null || true
iptables -F INPUT  2>/dev/null || true

# ---- Allow loopback -----------------------------------------
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A INPUT  -i lo -j ACCEPT

# ---- Allow established / related ----------------------------
iptables -A INPUT  -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# ---- Allow DNS (needed to re-resolve api.anthropic.com) -----
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# ---- Allow HTTPS to Anthropic resolved IPs ------------------
for ip in ${ANTHROPIC_IPS}; do
    echo "[network] Allowing HTTPS to ${ip}"
    iptables -A OUTPUT -p tcp -d "${ip}" --dport 443 -j ACCEPT
done

# ---- Allow ROS2 DDS -----------------------------------------
# DDS unicast range and multicast group used by Fast-DDS / Cyclone
iptables -A OUTPUT -p udp --dport 7400:7500 -j ACCEPT
iptables -A INPUT  -p udp --dport 7400:7500 -j ACCEPT
iptables -A OUTPUT -p udp -d 239.255.0.1   -j ACCEPT  # DDS multicast

# ---- Allow all traffic to/from ROS network subnet -----------
iptables -A OUTPUT -d "${ROS_SUBNET}" -j ACCEPT
iptables -A INPUT  -s "${ROS_SUBNET}" -j ACCEPT

# ---- Drop everything else outbound --------------------------
iptables -A OUTPUT -j DROP

echo "[network] Done. Allowed egress: DNS + Anthropic API + ROS DDS on ${ROS_SUBNET}"
