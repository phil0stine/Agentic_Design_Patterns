"""Tests for GoalManager — no ROS2 required."""
import pytest
from agent.goal_manager import GoalManager


def test_initial_state():
    gm = GoalManager()
    assert not gm.is_terminal()
    assert not gm.succeeded()
    assert not gm.failed()


def test_set_goal():
    gm = GoalManager()
    gm.set_goal({"name": "test"})
    assert not gm.is_terminal()


def test_declare_complete():
    gm = GoalManager()
    gm.set_goal({"name": "test"})
    gm.declare_complete()
    assert gm.is_terminal()
    assert gm.succeeded()
    assert not gm.failed()


def test_declare_failed():
    gm = GoalManager()
    gm.set_goal({"name": "test"})
    gm.declare_failed("hit a wall")
    assert gm.is_terminal()
    assert gm.failed()
    assert not gm.succeeded()
    assert gm.failure_reason == "hit a wall"


def test_complete_is_terminal():
    gm = GoalManager()
    gm.set_goal({"name": "x"})
    gm.declare_complete()
    assert gm.is_terminal()
