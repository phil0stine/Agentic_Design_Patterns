"""Tool registry — registers all tools and exposes them to Claude."""

from __future__ import annotations

import logging
from typing import Any, Callable

from agent.tools.navigation import navigation_tools
from agent.tools.perception import perception_tools
from agent.tools.system import system_tools

log = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(self, schema: dict, handler: Callable) -> None:
        self._tools[schema["name"]] = {"schema": schema, "handler": handler}

    def anthropic_schemas(self) -> list[dict]:
        """Return tool definitions in Anthropic API format."""
        return [v["schema"] for v in self._tools.values()]

    def call(self, name: str, inputs: dict) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name!r}")
        return self._tools[name]["handler"](**inputs)


def build_tool_registry(ros, goal_manager) -> ToolRegistry:
    registry = ToolRegistry()
    for schema, handler in navigation_tools(ros):
        registry.register(schema, handler)
    for schema, handler in perception_tools(ros):
        registry.register(schema, handler)
    for schema, handler in system_tools(goal_manager):
        registry.register(schema, handler)
    return registry
