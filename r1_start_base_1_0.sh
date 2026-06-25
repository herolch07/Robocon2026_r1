#!/usr/bin/env bash
set -e

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SESSION="r1_control"

# Keep R1 isolated from R2 or other ROS2 robots on the same network.
export ROS_DOMAIN_ID=1
export ROS_LOCALHOST_ONLY=1

if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux is not installed. Install it first:"
    echo "sudo apt install tmux"
    exit 1
fi

if [ ! -f "$WS_DIR/install/setup.bash" ]; then
    echo "Cannot find $WS_DIR/install/setup.bash"
    echo "Build the workspace first:"
    echo "cd $WS_DIR"
    echo "colcon build --symlink-install"
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists."
    echo "Attach with:"
    echo "tmux attach -t $SESSION"
    echo ""
    read -r -p "Kill old session and restart? [y/N] " answer
    case "$answer" in
        y|Y|yes|YES)
            tmux kill-session -t "$SESSION"
            ;;
        *)
            exit 0
            ;;
    esac
fi

BASE_CMD="cd $WS_DIR && source install/setup.bash"

tmux new-session -d -s "$SESSION" -n "joystick" \
    "$BASE_CMD && ros2 run my_joystick_driver joystick_node; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:1" -n "op_mode" \
    "$BASE_CMD && ros2 run operation_mode_control operation_mode_selector_node; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:2" -n "base_bridge" \
    "$BASE_CMD && ros2 run joystick_bridge joystick_bridge; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:3" -n "motors" \
    "$BASE_CMD && ros2 run base_omniwheel_r2_700 damiao_node; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:4" -n "nav" \
    "$BASE_CMD && ros2 run base_omniwheel_r2_700 local_navigation_node; exec bash"

tmux new-window -t "$SESSION:5" -n "elevator" \
    "$BASE_CMD && ros2 run r1_arm_control elevator_controller_node; exec bash"

tmux new-window -t "$SESSION:6" -n "elev_bridge" \
    "$BASE_CMD && ros2 run r1_arm_control elevator_joystick_bridge_node; exec bash"

tmux new-window -t "$SESSION:7" -n "horizontal" \
    "$BASE_CMD && ros2 run r1_arm_control horizontal_controller_node; exec bash"

tmux new-window -t "$SESSION:8" -n "horiz_bridge" \
    "$BASE_CMD && ros2 run r1_arm_control horizontal_joystick_bridge_node; exec bash"

tmux new-window -t "$SESSION:9" -n "motor7_pos" \
    "$BASE_CMD && ros2 run r1_arm_control motor7_position_controller_node; exec bash"

tmux new-window -t "$SESSION:10" -n "motor8_pos" \
    "$BASE_CMD && ros2 run r1_arm_control motor8_position_controller_node; exec bash"

tmux new-window -t "$SESSION:11" -n "motor_select" \
    "$BASE_CMD && ros2 run r1_arm_control motor_position_selector_joystick_bridge_node; exec bash"

tmux new-window -t "$SESSION:12" -n "relay_panel" \
    "$BASE_CMD && ros2 run kfs_staff_gripper kfs_staff_gripper_arduino_node; exec bash"

tmux new-window -t "$SESSION:13" -n "pneu_bridge" \
    "$BASE_CMD && ros2 run arduino_pneumatic_driver pneumatic_gripper_joystick_bridge_node; exec bash"

tmux new-window -t "$SESSION:14" -n "kfs_bridge" \
    "$BASE_CMD && ros2 run kfs_staff_gripper kfs_staff_gripper_joystick_bridge_node; exec bash"

tmux new-window -t "$SESSION:15" -n "power_shutdown" \
    "$BASE_CMD && ros2 run robot_power_control joystick_shutdown_node --ros-args -p dry_run:=false; exec bash"

tmux new-window -t "$SESSION:16" -n "monitor" \
    "$BASE_CMD && echo 'Monitor commands:' && echo 'ros2 node list' && echo 'ros2 topic echo /joystick_data' && echo 'ros2 topic echo /operation_mode' && echo 'ros2 topic echo /local_driving' && echo 'ros2 topic echo /elevator_speed_cmd' && echo 'ros2 topic echo /horizontal_speed_cmd' && echo 'ros2 topic echo /motor_position_selector_status' && echo 'ros2 topic echo /motor7_position_status' && echo 'ros2 topic echo /motor8_position_status' && echo 'ros2 topic echo /pneumatic_gripper_cmd' && echo 'ros2 topic echo /kfs_staff_gripper_cmd' && echo 'ros2 topic echo /kfs_staff_gripper_status' && echo 'ros2 topic echo /robot_power_status' && echo 'ros2 topic echo /damiao_control' && echo 'ros2 topic echo /damiao_motor_status' && echo 'ros2 param get /joystick_bridge max_speed_cm' && exec bash"

tmux select-window -t "$SESSION:16"

echo "Started R1 control system in tmux session '$SESSION'."
echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "ROS_LOCALHOST_ONLY=$ROS_LOCALHOST_ONLY"
echo ""
echo "Attach:"
echo "tmux attach -t $SESSION"
echo ""
echo "Stop all:"
echo "tmux kill-session -t $SESSION"

if [ "${R1_NO_TMUX_ATTACH:-0}" = "1" ]; then
    echo ""
    echo "R1_NO_TMUX_ATTACH=1, leaving tmux session detached."
else
    tmux attach -t "$SESSION"
fi
