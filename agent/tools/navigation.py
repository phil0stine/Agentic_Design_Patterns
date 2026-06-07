"""Navigation tools exposed to Claude."""

from __future__ import annotations

import math
from typing import Callable


def navigation_tools(ros) -> list[tuple[dict, Callable]]:
    return [
        (
            {
                "name": "send_nav_goal",
                "description": (
                    "Send a navigation goal to Nav2 (NavigateToPose action). "
                    "The robot will plan and drive to the target pose in the map frame. "
                    "Returns immediately after the goal is accepted; the robot navigates async."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "number",
                            "description": "Target X position in map frame (meters).",
                        },
                        "y": {
                            "type": "number",
                            "description": "Target Y position in map frame (meters).",
                        },
                        "yaw_deg": {
                            "type": "number",
                            "description": (
                                "Desired heading at the goal in degrees. "
                                "0 = +X axis, 90 = +Y axis. Default 0."
                            ),
                            "default": 0.0,
                        },
                    },
                    "required": ["x", "y"],
                },
            },
            lambda x, y, yaw_deg=0.0: _send_nav_goal(ros, x, y, yaw_deg),
        ),
        (
            {
                "name": "stop_robot",
                "description": "Immediately stop the robot by publishing zero velocity on /cmd_vel.",
                "input_schema": {"type": "object", "properties": {}},
            },
            lambda: ros.stop(),
        ),
        (
            {
                "name": "get_robot_pose",
                "description": "Return the robot's current pose from odometry (x, y, z, quaternion).",
                "input_schema": {"type": "object", "properties": {}},
            },
            lambda: ros.get_state_snapshot().get("odometry"),
        ),
    ]


def _send_nav_goal(ros, x: float, y: float, yaw_deg: float) -> dict:
    yaw_rad = math.radians(float(yaw_deg))
    qz = math.sin(yaw_rad / 2.0)
    qw = math.cos(yaw_rad / 2.0)
    return ros.send_nav_goal(x=x, y=y, qz=qz, qw=qw)
