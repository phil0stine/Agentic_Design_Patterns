#!/usr/bin/env python3
"""Entry point for the offline autonomy agent."""

from __future__ import annotations

import argparse
import logging
import os
import sys

import yaml
import rclpy

from agent.autonomy_agent import AutonomyAgent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline autonomy agent")
    p.add_argument("--mode", choices=["sitl", "bitl"], required=True,
                   help="Operating mode")
    p.add_argument("--goal", required=True,
                   help="Path to goal YAML file")
    p.add_argument("--config", default="/app/config/agent.yaml",
                   help="Path to agent config YAML")
    return p.parse_args()


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, os.environ.get("AGENT_LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger("agent.main")

    config = load_yaml(args.config)
    goal = load_yaml(args.goal)

    config["mode"] = args.mode
    config["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]

    log.info(
        "Starting | mode=%s goal=%s model=%s",
        args.mode,
        goal.get("name", "unnamed"),
        config.get("model", "claude-opus-4-8"),
    )

    rclpy.init()
    try:
        agent = AutonomyAgent(config)
        agent.run(goal)
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
