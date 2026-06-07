"""ROS2 interface — subscriptions, publishers, and action clients."""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Any

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import NavSatFix, Imu, LaserScan
from nav_msgs.msg import Odometry

log = logging.getLogger(__name__)


class ROSInterface(Node):
    """
    ROS2 node that caches the latest sensor data and exposes
    command methods for the agent tools to call.

    Topics are configurable via config["ros"]["topics"].
    Extend this class with your stack's custom message types.
    """

    SPIN_WAIT_S = 2.0  # time to let subscriptions populate after init

    def __init__(self, config: dict) -> None:
        super().__init__("autonomy_agent")
        self._config = config
        self._lock = threading.Lock()

        ros_cfg = config.get("ros", {})
        topics = ros_cfg.get("topics", {})

        # ---- State cache ----------------------------------------
        self._odom: dict | None = None
        self._gps: dict | None = None
        self._imu: dict | None = None
        self._scan: dict | None = None

        # ---- Subscribers ----------------------------------------
        self.create_subscription(
            Odometry, topics.get("odom", "/odom"), self._odom_cb, 10
        )
        self.create_subscription(
            NavSatFix, topics.get("gps", "/gps/fix"), self._gps_cb, 10
        )
        self.create_subscription(
            Imu, topics.get("imu", "/imu/data"), self._imu_cb, 10
        )
        self.create_subscription(
            LaserScan, topics.get("scan", "/scan"), self._scan_cb, 10
        )

        # ---- Publishers -----------------------------------------
        self._cmd_vel_pub = self.create_publisher(
            Twist, topics.get("cmd_vel", "/cmd_vel"), 10
        )

        # ---- Nav2 action client ---------------------------------
        nav2_action = ros_cfg.get("nav2_action", "navigate_to_pose")
        self._nav_client = ActionClient(self, NavigateToPose, nav2_action)

        # ---- Spin in background thread --------------------------
        self._executor = MultiThreadedExecutor()
        self._executor.add_node(self)
        self._spin_thread = threading.Thread(
            target=self._executor.spin, daemon=True
        )
        self._spin_thread.start()

        log.info("ROSInterface online, waiting %.1fs for topics...", self.SPIN_WAIT_S)
        time.sleep(self.SPIN_WAIT_S)

    # ------------------------------------------------------------------ #
    # State snapshot                                                       #
    # ------------------------------------------------------------------ #

    def get_state_snapshot(self) -> dict:
        with self._lock:
            return {
                "timestamp_s": time.time(),
                "odometry": self._odom,
                "gps": self._gps,
                "imu_orientation": self._imu,
                "lidar_summary": self._scan,
            }

    # ------------------------------------------------------------------ #
    # Commands                                                             #
    # ------------------------------------------------------------------ #

    def send_nav_goal(
        self,
        x: float,
        y: float,
        z: float = 0.0,
        qx: float = 0.0,
        qy: float = 0.0,
        qz: float = 0.0,
        qw: float = 1.0,
        frame_id: str = "map",
    ) -> dict:
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            return {"success": False, "error": "Nav2 action server not available"}

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = float(z)
        goal_msg.pose.pose.orientation.x = float(qx)
        goal_msg.pose.pose.orientation.y = float(qy)
        goal_msg.pose.pose.orientation.z = float(qz)
        goal_msg.pose.pose.orientation.w = float(qw)

        future = self._nav_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
        if not future.done():
            return {"success": False, "error": "Timeout waiting for goal acceptance"}

        handle = future.result()
        if not handle or not handle.accepted:
            return {"success": False, "error": "Goal rejected by Nav2"}

        return {"success": True, "goal_id": str(handle.goal_id)}

    def publish_cmd_vel(
        self,
        linear_x: float = 0.0,
        linear_y: float = 0.0,
        angular_z: float = 0.0,
    ) -> dict:
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.linear.y = float(linear_y)
        msg.angular.z = float(angular_z)
        self._cmd_vel_pub.publish(msg)
        return {"published": True, "linear_x": linear_x, "angular_z": angular_z}

    def stop(self) -> dict:
        return self.publish_cmd_vel(0.0, 0.0, 0.0)

    # ------------------------------------------------------------------ #
    # Callbacks                                                            #
    # ------------------------------------------------------------------ #

    def _odom_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose
        with self._lock:
            self._odom = {
                "x": p.position.x,
                "y": p.position.y,
                "z": p.position.z,
                "qx": p.orientation.x,
                "qy": p.orientation.y,
                "qz": p.orientation.z,
                "qw": p.orientation.w,
            }

    def _gps_cb(self, msg: NavSatFix) -> None:
        with self._lock:
            self._gps = {
                "latitude": msg.latitude,
                "longitude": msg.longitude,
                "altitude": msg.altitude,
                "status": msg.status.status,
            }

    def _imu_cb(self, msg: Imu) -> None:
        o = msg.orientation
        with self._lock:
            self._imu = {"qx": o.x, "qy": o.y, "qz": o.z, "qw": o.w}

    def _scan_cb(self, msg: LaserScan) -> None:
        valid = [
            r for r in msg.ranges
            if msg.range_min < r < msg.range_max
        ]
        with self._lock:
            self._scan = {
                "min_range_m": round(min(valid), 3) if valid else None,
                "max_range_m": round(max(valid), 3) if valid else None,
                "num_valid_rays": len(valid),
                "total_rays": len(msg.ranges),
            }
