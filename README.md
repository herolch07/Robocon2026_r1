# Robocon R1 ROS 2 Workspace

English | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

This repository contains the current R1 robot control workspace developed by EdUHK Robotics Team @ Hero.

- GitHub: `herolch07`
- Current final operation guide: [r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md)
- System architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Node/topic graph: [NODE_GRAPH.md](NODE_GRAPH.md)
- Chassis speed tuning notes: [SPEED_TUNING.md](SPEED_TUNING.md)
- Main startup script: `./r1_start_base_1_0.sh`
- Confirmed current date in the project notes: 2026-05-22

## Current System

The workspace is a ROS 2 control system for the Robocon R1 robot:

- Motor 1-4: four-wheel omni base
- Motor 5: elevator actuator
- Motor 6: horizontal actuator
- Motor 7: arm gripper motor
- Arduino pneumatic gripper: gripper open/close and height high/low
- 8BitDo controller input through Linux `evdev`
- Optional keyboard teleoperation package for low-speed debugging

## Controller Mapping

```text
Left stick up/down: base forward/backward
Left stick left/right: base left/right strafe
Right stick left/right: base in-place rotation
R1 / L1: Motor 5 elevator forward/reverse at fixed speed
D-pad left/right: Motor 6 horizontal movement
D-pad up/down: Motor 6 horizontal power level 0.2 / 0.5 / 1.0
START / SELECT: currently unused for chassis speed
R2 / L2: Motor 7 arm gripper analog forward/reverse
B: arm pneumatic gripper OPEN while held, CLOSE when released
A: arm pneumatic height LOW latch
X: arm pneumatic height HIGH latch
Y: KFS staff gripper OPEN while held, CLOSE when released
R3: currently unused
```

## Important Current Defaults

```text
Joystick axis range: -512 .. 512
Trigger range: 0 .. 512
Joystick deadzone: 15
joystick_bridge max_speed_cm: 150.0
joystick_bridge max_rotation: 1.2
joystick_bridge translation_linear_weight: 0.1
joystick_bridge rotation_linear_weight: 0.1
arm gripper max_speed_rad_s: 1.3
arm gripper gripper_linear_weight: 0.1
local_navigation_node max_wheel_speed_rad_s: 64.0
joystick_bridge input_timeout_sec: 0.3
local_navigation_node command_timeout_sec: 0.3
damiao_node command_timeout_sec: 0.5
pneumatic safe_state: [0, 1] = LOW + CLOSE
```

Base kinematics defaults:

```text
Motor 1 = left front
Motor 2 = right front
Motor 3 = right rear
Motor 4 = left rear

lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4 = [1, 1, -1, -1]
lateral_coeff_1..4 = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

## Quick Start

On the robot host:

```bash
cd /home/robotics/robocon/new_ws
colcon build --symlink-install
source install/setup.bash
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

The script starts a tmux session named:

```text
r1_control
```

Common tmux commands:

```text
Attach: tmux attach -t r1_control
Detach: Ctrl+b, then d
Stop all: tmux kill-session -t r1_control
```

## Package Map

```text
src/my_joystick_msgs          Custom Joystick message
src/my_joystick_driver        evdev joystick driver, publishes /joystick_data
src/joystick_bridge           joystick to /local_driving bridge
src/base_omniwheel_r2_700     omni base kinematics and DM motor driver
src/r1_arm_control            Motor 5/6/7 speed controllers and joystick bridges
src/kfs_staff_gripper         KFS/arm pneumatic three-relay Arduino aggregator
src/arduino_pneumatic_driver  Arduino relay pneumatic gripper joystick bridge
src/keyboard_teleop           keyboard debugging teleoperation
```

## Safety Layers

The current control chain contains multiple watchdogs:

- `joystick_bridge`: publishes `/local_driving = [0, 0, 0]` if `/joystick_data` times out.
- `local_navigation_node`: sends zero speed to Motor 1-4 if `/local_driving` times out.
- `damiao_node`: sends zero velocity to timed-out motors for continuous VEL commands.
- `r1_arm_control` controllers: zero their actuator speed when command topics time out.
- `arduino_pneumatic_driver`: sends `safe_state = [0, 1]` on command timeout, reconnect, and shutdown.

## Notes About Older Documents

Some reports in this workspace are historical records. If a document mentions `±8192`, `410` joystick deadzone, `100 cm/s` default base speed, `start_all_nodes.sh`, `start_full_control_chain.sh`, VESC nodes, or the old `Robocon2026_r2/2026R2_ws` path, treat that section as legacy unless it is explicitly marked as current.

For the current robot operation flow, use this README and [r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md).

## ROS2 Network Isolation

R1 startup uses an isolated ROS2 environment by default:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

This prevents R1 from discovering R2 nodes such as `/damiao_motor_controller`, `/global_navigation_node`, and `/base/dummy_control`. See `ROS_DOMAIN_ISOLATION.md` before changing these values.

## Damiao E-stop Recovery

The motor driver now detects stale/disabled Motor 1-7 feedback, retries `VEL + enable + zero` every 2 seconds, and blocks non-zero commands until enabled feedback is confirmed and the controller returns to neutral. Monitor `/damiao_motor_status`; state codes are `0=RECOVERING`, `1=WAIT_NEUTRAL`, `2=READY`, `3=DISABLED`.
