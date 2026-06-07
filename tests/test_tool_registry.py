"""Tests for tool registry and system tools — no ROS2 required."""
import pytest
from unittest.mock import MagicMock
from agent.tools import ToolRegistry
from agent.tools.system import system_tools
from agent.goal_manager import GoalManager


def test_register_and_call():
    registry = ToolRegistry()
    handler = MagicMock(return_value={"ok": True})
    schema = {
        "name": "my_tool",
        "description": "test",
        "input_schema": {"type": "object", "properties": {}},
    }
    registry.register(schema, handler)
    result = registry.call("my_tool", {})
    handler.assert_called_once()
    assert result == {"ok": True}


def test_unknown_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.call("nonexistent", {})


def test_anthropic_schemas_format():
    registry = ToolRegistry()
    schema = {
        "name": "a_tool",
        "description": "desc",
        "input_schema": {"type": "object", "properties": {}},
    }
    registry.register(schema, lambda: None)
    schemas = registry.anthropic_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "a_tool"


def test_declare_goal_complete_via_tool():
    gm = GoalManager()
    gm.set_goal({"name": "x"})
    tools = dict(system_tools(gm))

    # find declare_goal_complete handler
    complete_schema = next(s for s, _ in system_tools(gm) if s["name"] == "declare_goal_complete")
    complete_handler = dict((s["name"], h) for s, h in system_tools(gm))["declare_goal_complete"]

    result = complete_handler(summary="done")
    assert result["status"] == "goal_complete"
    assert gm.succeeded()


def test_declare_goal_failed_via_tool():
    gm = GoalManager()
    gm.set_goal({"name": "x"})
    failed_handler = dict((s["name"], h) for s, h in system_tools(gm))["declare_goal_failed"]
    result = failed_handler(reason="blocked")
    assert result["status"] == "goal_failed"
    assert gm.failed()
    assert gm.failure_reason == "blocked"
