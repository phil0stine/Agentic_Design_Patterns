# Offline Autonomy Stack

A fully self-contained autonomy agent that runs inside Docker, connects to **Claude** (via the Anthropic API) as its reasoning brain, interfaces with **ROS2 Jazzy**, and uses **GTSAM** for state estimation. Network access inside the container is locked to `api.anthropic.com` only — no other internet egress.

Two operating modes:
- **SITL** — Software In The Loop: agent drives a live simulator
- **BITL** — Bag In The Loop: agent analyzes/reacts to a recorded ROS2 bag

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Docker Container                     │
│                                                          │
│  ┌─────────────────┐    iptables     ┌────────────────┐  │
│  │  AutonomyAgent  │◄──────────────►│  api.anthropic │  │
│  │  (Python)       │  (only egress) │  .com (HTTPS)  │  │
│  └────────┬────────┘                └────────────────┘  │
│           │ rclpy                                        │
│  ┌────────▼────────┐                                     │
│  │  ROSInterface   │◄── /odom, /gps, /scan, /imu        │
│  │  (Node)         │──► /cmd_vel, navigate_to_pose       │
│  └─────────────────┘                                     │
│                                                          │
│  Net policy: loopback + ROS DDS subnet + Anthropic API   │
└──────────────────────────────────────────────────────────┘
           │ host networking (ROS2 DDS)
           ▼
   Simulator / Bag Player (external)
```

### Agent Loop

```
Goal YAML ──► system prompt
    │
    └─► loop until terminal:
          1. Snapshot robot state (odom, GPS, LiDAR, IMU)
          2. Build user message with state JSON
          3. Call Claude (tool_use enabled)
          4. Execute tool calls via ROSInterface
          5. Append results; repeat
          └─► Claude calls declare_goal_complete / declare_goal_failed
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker 24+ with BuildKit | `docker buildx` required for multi-arch |
| NVIDIA Container Toolkit | For GPU access inside container |
| `ANTHROPIC_API_KEY` | Set in `.env` file |
| ROS2 Jazzy on host | Only needed if running stack natively; Docker handles it otherwise |
| SITL: running simulator | Gazebo, Webots, AirSim, or custom — must publish ROS2 topics |
| BITL: ROS2 bag file | `.db3` or MCAP format |

---

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/phil0stine/agentic_design_patterns.git
cd agentic_design_patterns
git checkout claude/offline-autonomy-claude-integration-oH3GM

cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and other vars
```

### 2. Build the image

```bash
# x86_64
bash scripts/build.sh x86 autonomy-stack:latest

# ARM64 / Jetson (JetPack 7.2) — run this ON the Jetson or via cross-compile
bash scripts/build.sh arm64 autonomy-stack:latest
```

> **ARM / JetPack 7.2 note:** The base image is
> `nvcr.io/nvidia/l4t-pytorch:2.12-jp7.2-py3`. Verify the exact tag at
> https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-pytorch before
> building. PyTorch is pre-installed in the NGC base; the Dockerfile skips
> the separate PyTorch install step on ARM.

### 3. Run SITL

```bash
# Ensure simulator is running and publishing to ROS_DOMAIN_ID=0
export ANTHROPIC_API_KEY=sk-ant-...
bash scripts/run_sitl.sh config/goals/example_sitl_goal.yaml
```

### 4. Run BITL

```bash
export ANTHROPIC_API_KEY=sk-ant-...
bash scripts/run_bitl.sh /path/to/bags my_bag.db3 config/goals/example_bitl_goal.yaml
```

---

## Environment File (`.env`)

Create `.env` in the repo root:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# ROS2
ROS_DOMAIN_ID=0

# SITL: address where simulator is reachable (if not host networking)
SIMULATOR_HOST=localhost

# BITL
BAG_PATH=/absolute/path/to/bag/dir
BAG_FILE=my_recording          # name of the .db3 / directory
BAG_RATE=1.0                   # playback speed multiplier
BAG_LOOP=--loop                # remove to play once

# Agent
AGENT_LOG_LEVEL=INFO           # DEBUG for verbose tool call logs

# Network (set to false only for debugging)
RESTRICT_NETWORK=true

# Subnet where ROS2 DDS traffic is allowed (loopback + LAN)
ROS_NETWORK_SUBNET=192.168.1.0/24
```

---

## Writing Goals

Goals are YAML files under `config/goals/`. The agent reads them at startup and builds its system prompt from them.

```yaml
name: my_goal                    # short identifier

description: |
  A plain-English description of what the robot should do.
  This becomes part of the Claude system prompt verbatim.

success_criteria: |
  Specific, measurable conditions that define success.
  Claude will call declare_goal_complete when these are met.

constraints:
  - Do not exceed 1.0 m/s
  - Maintain 0.5 m clearance from obstacles
  - Complete within 10 minutes

parameters:                      # arbitrary — included in state context
  waypoints:
    - {x: 5.0, y: 0.0}
    - {x: 10.0, y: 5.0}
  arrival_tolerance_m: 0.5
```

Mount your goal file into the container via the volume in `docker-compose.*.yml`, or build it into the image.

---

## Connecting to Your Stack

The `ROSInterface` in `agent/ros_interface.py` subscribes to standard topic names. To wire in your stack:

1. **Remap topics** — set the `topics` block in `config/agent.yaml` to match your stack's actual topic names.
2. **Add subscribers** — extend `ROSInterface` with any stack-specific message types (e.g., custom perception outputs, mission status topics).
3. **Add tools** — add new tool definitions under `agent/tools/` and register them in `agent/tools/__init__.py`.
4. **Mount your workspace** — if your stack has compiled ROS2 packages, mount the install directory and source it in `docker/entrypoint.sh`.

Example entrypoint addition for a custom workspace:

```bash
# In docker/entrypoint.sh, after the ROS2 source line:
if [[ -f /workspace/install/setup.bash ]]; then
    source /workspace/install/setup.bash
fi
```

Example `docker-compose.sitl.yml` volume mount:

```yaml
volumes:
  - /path/to/your/ros2_ws/install:/workspace/install:ro
```

---

## Network Policy Details

`docker/network/restrict_network.sh` (run by the entrypoint) applies these `iptables` rules:

| Direction | Allowed |
|---|---|
| Outbound | DNS (UDP/TCP 53) |
| Outbound | HTTPS (TCP 443) to resolved IPs of `api.anthropic.com` |
| Outbound | UDP 7400–7500 (ROS2 DDS) |
| Outbound | All to `ROS_NETWORK_SUBNET` (loopback + LAN) |
| Inbound | Established/related |
| Inbound | All from `ROS_NETWORK_SUBNET` |
| Everything else | DROP |

The container needs `CAP_NET_ADMIN` (set in compose files). If running without that capability, set `RESTRICT_NETWORK=false` and manage firewall rules at the host level instead.

> **Important:** DNS is allowed outbound so `api.anthropic.com` can be re-resolved at runtime (Anthropic may rotate IPs). If you want stricter control, pre-resolve the IPs at image build time and remove the DNS rule.

---

## Available Agent Tools

The following tools are exposed to Claude:

| Tool | Description |
|---|---|
| `send_nav_goal` | Send a Nav2 NavigateToPose goal (x, y, yaw_deg) |
| `stop_robot` | Publish zero velocity |
| `get_robot_pose` | Read current odometry |
| `get_lidar_summary` | Min/max range + obstacle count from latest scan |
| `get_gps` | Current GPS fix |
| `get_full_state` | Complete sensor snapshot |
| `log_status` | Record an observation or plan step |
| `declare_goal_complete` | Signal success (terminates loop) |
| `declare_goal_failed` | Signal failure with reason (terminates loop) |

Add more tools by creating functions in `agent/tools/` and registering them in `agent/tools/__init__.py`.

---

## Multi-Arch Build Notes

### x86_64
- Base: `nvidia/cuda:12.4.1-cudnn-devel-ubuntu24.04`
- PyTorch installed from `pytorch.org/whl/cu124`
- Build natively or via `docker buildx`

### ARM64 / Jetson JetPack 7.2
- Base: `nvcr.io/nvidia/l4t-pytorch:2.12-jp7.2-py3` (Ubuntu 24.04, CUDA 13.x)
- PyTorch **already included** in the NGC base image — no separate install
- Must build on the Jetson itself, or use `docker buildx` with QEMU
- GTSAM is compiled from source in both cases

```bash
# Cross-compile from x86 (slow; QEMU emulation)
docker buildx create --use --name multiarch
docker buildx build --platform linux/arm64 \
    -f docker/Dockerfile.arm64 \
    -t autonomy-stack:arm64 --load .

# Faster: build directly on the Jetson
scp -r . jetson:/tmp/autonomy/
ssh jetson 'cd /tmp/autonomy && bash scripts/build.sh arm64'
```

---

## Troubleshooting

**Agent can't reach `api.anthropic.com`**
- Check `RESTRICT_NETWORK=true` and that `CAP_NET_ADMIN` is set in the compose file
- Run `docker exec <container> iptables -L OUTPUT -v` to inspect rules
- DNS resolution happens at container start; if the IP rotated, restart the container

**ROS2 topics not received**
- Confirm `ROS_DOMAIN_ID` matches the simulator
- With host networking (`network_mode: host`) DDS discovery is automatic
- If using bridge networking, expose ports 7400-7500 UDP and set `RMW_FASTRTPS_DISABLE_SHAREDMEMORY=1`

**GTSAM build fails**
- On ARM, TBB may need `sudo apt install libtbb-dev` from NVIDIA's L4T apt mirror
- Set `-DGTSAM_USE_SYSTEM_EIGEN=OFF` if Eigen version conflicts arise

**Nav2 action server not found**
- Ensure Nav2 is fully launched before the agent starts (add a `depends_on` healthcheck or pre-sleep)
- Check with `ros2 action list` inside the container
