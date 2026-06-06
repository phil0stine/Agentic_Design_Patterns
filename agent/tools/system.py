"""System tools: goal lifecycle and logging."""

from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger("agent.status")


def system_tools(goal_manager) -> list[tuple[dict, Callable]]:
    return [
        (
            {
                "name": "declare_goal_complete",
                "description": (
                    "Declare that the high-level goal has been successfully achieved. "
                    "Call this only when all success criteria defined in the goal are satisfied. "
                    "This terminates the agent loop."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Brief description of how the goal was achieved.",
                        }
                    },
                    "required": ["summary"],
                },
            },
            lambda summary: _complete(goal_manager, summary),
        ),
        (
            {
                "name": "declare_goal_failed",
                "description": (
                    "Declare that the goal cannot be achieved. "
                    "Use when a blocking condition is encountered that cannot be recovered from. "
                    "This terminates the agent loop."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Clear explanation of why the goal could not be achieved.",
                        }
                    },
                    "required": ["reason"],
                },
            },
            lambda reason: _fail(goal_manager, reason),
        ),
        (
            {
                "name": "log_status",
                "description": (
                    "Record an observation, decision, or intermediate result to the agent log. "
                    "Use liberally to create an auditable trace of reasoning."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Status message to record.",
                        }
                    },
                    "required": ["message"],
                },
            },
            lambda message: _log_status(message),
        ),
    ]


def _complete(goal_manager, summary: str) -> dict:
    goal_manager.declare_complete()
    return {"status": "goal_complete", "summary": summary}


def _fail(goal_manager, reason: str) -> dict:
    goal_manager.declare_failed(reason)
    return {"status": "goal_failed", "reason": reason}


def _log_status(message: str) -> dict:
    log.info(message)
    return {"logged": True}
