"""Tracks high-level goal lifecycle."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class GoalManager:
    """Simple FSM: idle -> running -> (succeeded | failed)."""

    def __init__(self) -> None:
        self._goal: dict | None = None
        self._status: str = "idle"
        self.failure_reason: str = ""

    def set_goal(self, goal: dict) -> None:
        self._goal = goal
        self._status = "running"
        log.info("Goal set: %s", goal.get("name"))

    def declare_complete(self) -> None:
        self._status = "succeeded"
        log.info("Goal SUCCEEDED")

    def declare_failed(self, reason: str) -> None:
        self._status = "failed"
        self.failure_reason = reason
        log.error("Goal FAILED: %s", reason)

    def is_terminal(self) -> bool:
        return self._status in ("succeeded", "failed")

    def succeeded(self) -> bool:
        return self._status == "succeeded"

    def failed(self) -> bool:
        return self._status == "failed"
