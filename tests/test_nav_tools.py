"""Tests for navigation tool input validation."""
import math
from unittest.mock import MagicMock
from agent.tools.navigation import navigation_tools, _send_nav_goal


def make_mock_ros():
    ros = MagicMock()
    ros.send_nav_goal.return_value = {"success": True, "goal_id": "abc"}
    ros.stop.return_value = {"published": True}
    return ros


def test_send_nav_goal_yaw_conversion():
    ros = make_mock_ros()
    _send_nav_goal(ros, x=1.0, y=2.0, yaw_deg=90.0)
    call_kwargs = ros.send_nav_goal.call_args[1]
    # 90 degrees -> qz = sin(45°) ≈ 0.707, qw = cos(45°) ≈ 0.707
    assert abs(call_kwargs["qz"] - math.sin(math.radians(45))) < 1e-6
    assert abs(call_kwargs["qw"] - math.cos(math.radians(45))) < 1e-6


def test_send_nav_goal_zero_yaw():
    ros = make_mock_ros()
    _send_nav_goal(ros, x=5.0, y=3.0, yaw_deg=0.0)
    call_kwargs = ros.send_nav_goal.call_args[1]
    assert abs(call_kwargs["qz"]) < 1e-9
    assert abs(call_kwargs["qw"] - 1.0) < 1e-9


def test_nav_tools_returns_correct_names():
    ros = make_mock_ros()
    tools = navigation_tools(ros)
    names = {schema["name"] for schema, _ in tools}
    assert "send_nav_goal" in names
    assert "stop_robot" in names
    assert "get_robot_pose" in names
