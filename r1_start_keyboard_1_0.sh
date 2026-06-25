#!/usr/bin/env bash
set -e

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SESSION="r1_keyboard_control"

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

tmux new-session -d -s "$SESSION" -n "keyboard" \
    "$BASE_CMD && ros2 run keyboard_teleop keyboard_teleop_node; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:1" -n "motors" \
    "$BASE_CMD && ros2 run base_omniwheel_r2_700 damiao_node; exec bash"

sleep 0.5

tmux new-window -t "$SESSION:2" -n "nav" \
    "$BASE_CMD && ros2 run base_omniwheel_r2_700 local_navigation_node; exec bash"

tmux new-window -t "$SESSION:3" -n "elevator" \
    "$BASE_CMD && ros2 run r1_arm_control elevator_controller_node; exec bash"

tmux new-window -t "$SESSION:4" -n "horizontal" \
    "$BASE_CMD && ros2 run r1_arm_control horizontal_controller_node; exec bash"

tmux new-window -t "$SESSION:5" -n "gripper" \
    "$BASE_CMD && ros2 run r1_arm_control arm_gripper_controller_node; exec bash"

tmux new-window -t "$SESSION:6" -n "pneumatic" \
    "$BASE_CMD && ros2 run arduino_pneumatic_driver pneumatic_relay_driver_node; exec bash"

tmux new-window -t "$SESSION:7" -n "monitor" \
    "$BASE_CMD && echo 'Monitor commands:' && echo 'ros2 node list' && echo 'ros2 topic echo /local_driving' && echo 'ros2 topic echo /elevator_speed_cmd' && echo 'ros2 topic echo /horizontal_speed_cmd' && echo 'ros2 topic echo /arm_gripper_speed_cmd' && echo 'ros2 topic echo /pneumatic_gripper_cmd' && echo 'ros2 topic echo /damiao_control' && exec bash"

tmux select-window -t "$SESSION:0"

echo "Started R1 keyboard control system in tmux session '$SESSION'."
echo ""
echo "Keyboard controls are in the first tmux window:"
echo "  Base: W/S forward/back, A/D left/right, Q/E rotate"
echo "  Elevator: I/K"
echo "  Horizontal: J/L"
echo "  Arm gripper motor: U/O"
echo "  Pneumatic: B open while held, H height high, N height low"
echo "  SPACE stop all, Ctrl+C quit"
echo ""
echo "Attach:"
echo "tmux attach -t $SESSION"
echo ""
echo "Stop all:"
echo "tmux kill-session -t $SESSION"

tmux attach -t "$SESSION"
