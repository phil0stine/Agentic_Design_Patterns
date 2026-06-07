"""Main autonomy agent — Claude-driven agentic loop over ROS2."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from agent.claude_interface import ClaudeInterface
from agent.ros_interface import ROSInterface
from agent.goal_manager import GoalManager
from agent.tools import build_tool_registry

log = logging.getLogger(__name__)


class AutonomyAgent:
    """
    Drives the robot toward a high-level goal by:
      1. Snapshotting robot state each iteration
      2. Sending state + history to Claude
      3. Executing Claude's tool calls via ROSInterface
      4. Repeating until Claude declares success or failure
    """

    MAX_ITERATIONS = 200
    LOOP_SLEEP_S = 1.0

    def __init__(self, config: dict) -> None:
        self.config = config
        self.claude = ClaudeInterface(config)
        self.ros = ROSInterface(config)
        self.goal_manager = GoalManager()
        self.tool_registry = build_tool_registry(self.ros, self.goal_manager)

    # ------------------------------------------------------------------ #
    # Main loop                                                            #
    # ------------------------------------------------------------------ #

    def run(self, goal: dict) -> None:
        log.info("Goal: %s", goal.get("name"))
        self.goal_manager.set_goal(goal)

        system_prompt = self._build_system_prompt(goal)
        history: list[dict[str, Any]] = []
        iteration = 0

        while not self.goal_manager.is_terminal() and iteration < self.MAX_ITERATIONS:
            iteration += 1
            log.info("--- Iteration %d / %d ---", iteration, self.MAX_ITERATIONS)

            state = self.ros.get_state_snapshot()
            history.append({
                "role": "user",
                "content": self._format_state_msg(state, iteration),
            })

            response = self.claude.complete(
                system=system_prompt,
                messages=history,
                tools=self.tool_registry.anthropic_schemas(),
            )

            log.debug("stop_reason=%s", response.stop_reason)

            # Record assistant turn
            history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_results = self._execute_tool_calls(response.content)
                history.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                text = _extract_text(response.content)
                if text:
                    log.info("Claude: %s", text)
                if not self.goal_manager.is_terminal():
                    log.warning(
                        "Claude ended turn without declaring completion — re-prompting."
                    )

            time.sleep(self.LOOP_SLEEP_S)

        # ---- Report outcome -------------------------------------
        if self.goal_manager.succeeded():
            log.info("SUCCESS: %s", goal.get("name"))
        elif self.goal_manager.failed():
            log.error("FAILED: %s | %s", goal.get("name"), self.goal_manager.failure_reason)
        else:
            log.error("MAX ITERATIONS reached without completion.")

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _build_system_prompt(self, goal: dict) -> str:
        mode = self.config.get("mode", "sitl")
        constraints = "\n".join(
            f"- {c}" for c in goal.get("constraints", ["Operate safely."])
        )
        params = json.dumps(goal.get("parameters", {}), indent=2)
        return f"""You are an autonomous robot agent operating in {mode.upper()} mode.

MISSION
{goal.get('description', '').strip()}

SUCCESS CRITERIA
{goal.get('success_criteria', '').strip()}

CONSTRAINTS
{constraints}

GOAL PARAMETERS
{params}

INSTRUCTIONS
- Each turn you receive a JSON snapshot of the current robot state.
- Reason step-by-step before acting. Use tools to read sensors and send commands.
- When all success criteria are satisfied, call `declare_goal_complete` with a summary.
- If the goal becomes impossible (hardware fault, blocked path, timeout), call
  `declare_goal_failed` with a clear reason.
- In BITL mode do not send navigation commands unless the goal explicitly requires it;
  focus on perception and analysis instead.
- Be conservative: prefer stopping and re-assessing over aggressive maneuvers.
"""

    def _format_state_msg(self, state: dict, iteration: int) -> str:
        return (
            f"[Iteration {iteration}] Robot state snapshot:\n"
            + json.dumps(state, indent=2, default=str)
        )

    def _execute_tool_calls(self, content: list) -> list[dict]:
        results = []
        for block in content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue
            log.info("Tool: %s(%s)", block.name, block.input)
            try:
                result = self.tool_registry.call(block.name, block.input)
                log.debug("Tool result: %s", result)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            except Exception as exc:
                log.error("Tool %s raised: %s", block.name, exc)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"ERROR: {exc}",
                    "is_error": True,
                })
        return results


def _extract_text(content: list) -> str:
    return " ".join(b.text for b in content if hasattr(b, "text") and b.text)
