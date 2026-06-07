"""Perception / sensor tools exposed to Claude."""

from __future__ import annotations

from typing import Callable


def perception_tools(ros) -> list[tuple[dict, Callable]]:
    return [
        (
            {
                "name": "get_lidar_summary",
                "description": (
                    "Return a summary of the latest LiDAR scan: min/max range "
                    "and number of valid rays. Useful for obstacle detection."
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
            lambda: ros.get_state_snapshot().get("lidar_summary"),
        ),
        (
            {
                "name": "get_gps",
                "description": (
                    "Return the current GPS fix: latitude, longitude, altitude, "
                    "and fix status (0=no fix, 1=fix, 2=DGPS)."
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
            lambda: ros.get_state_snapshot().get("gps"),
        ),
        (
            {
                "name": "get_full_state",
                "description": (
                    "Return the complete robot state snapshot: odometry, GPS, "
                    "IMU orientation, and LiDAR summary."
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
            lambda: ros.get_state_snapshot(),
        ),
    ]
