#!/usr/bin/env python3
"""Motor 7 entry point for the reusable three-position POS_VEL controller."""

import rclpy
from rclpy.executors import ExternalShutdownException

from r1_arm_control.motor8_position_controller_node import (
    Motor8PositionControllerNode,
)


class Motor7PositionControllerNode(Motor8PositionControllerNode):
    """Run the shared three-position controller with Motor 7 topics and identity."""

    def __init__(self):
        super().__init__(
            node_name="motor7_position_controller_node",
            default_motor_id=7,
            input_topic="/motor7_position_input",
            status_topic="/motor7_position_status",
        )


def main(args=None):
    rclpy.init(args=args)
    node = Motor7PositionControllerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
