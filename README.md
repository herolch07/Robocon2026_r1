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
cd /home/robotics/robocon2026_r1/r1_control_ws
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


## 2026-06-15 Current Operator-Frame Control

This section supersedes earlier current-operation text that assigns the D-pad to
Motor 6 or marks L3/R3 unused. Historical sections remain for traceability.

```text
D-pad up:    E-stop/front of robot faces operator-frame front, view=0
D-pad right: E-stop/front of robot faces operator-frame right, view=1
D-pad down:  E-stop/front of robot faces operator-frame back, view=2
D-pad left:  E-stop/front of robot faces operator-frame left, view=3
```

The D-pad only changes how left-stick translation is converted into the robot
body frame; it does not rotate the chassis. The left stick must be neutral before
a view change is accepted. Right-stick rotation and all chassis speed and
acceleration limits are unchanged.

Motor 6 horizontal control is now:

```text
L3: +10 rad/s
R3: -10 rad/s
L3 + R3 or neither: 0 rad/s
```

Monitor the selected view with `ros2 topic echo /view_orientation`. This feature
passed real-machine testing on 2026-06-15 and is the configuration to keep.

## 2026-06-16 8BitDo P1/P2 Back Paddle Mapping

P1/P2 are not independent ROS buttons in the current setup. `evtest` showed that
A/B/X/Y generate events, while P1/P2 do not generate separate events. The current
controller-side remap is:

```text
P1 = R3
P2 = L3
```

This means P1/P2 are alternate physical inputs for Motor 6 horizontal control:

```text
P1 -> R3 -> -10 rad/s
P2 -> L3 -> +10 rad/s
P1 + P2 or released -> 0 rad/s
```

No ROS message, topic, node, timeout, or controller logic changed for this mapping.

## 2026-06-18 Current Operation Update

This section is the latest operation summary. It supersedes older sections that describe the previous P1/P2 direction, relay7 as reserved, or manual startup as the only startup flow. Older sections remain for traceability.

```text
P1 = R3 -> Motor6 horizontal -10 rad/s
P2 = L3 -> Motor6 horizontal +10 rad/s
P1 + P2 or released -> Motor6 0 rad/s
```

Current seven-relay Arduino order:

```text
[relay1, relay2, relay3, relay4, relay5, relay6, relay7]
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

`/pneumatic_gripper_cmd` now has six values:

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

`SELECT/-` controls the inclination of the arm currently selected by `START/+`: Motor7 uses relay7 / Motor7 inclination, and Motor8 uses relay4 / Motor8 inclination.

Controller-gated autostart is available: `systemd/r1-control-autostart.service` starts `scripts/wait_and_start_robot.sh` at boot, and the watcher starts `r1_start_base_1_0.sh` only after an 8BitDo / Xbox controller is active. Default `STOP_ON_CONTROLLER_LOST=0` means a controller dropout does not kill the ROS tmux session; node watchdogs remain responsible for safe output.


## 2026-06-19 Current KFS-Gripper Operator-Frame Control

This section supersedes the 2026-06-15 E-stop-based D-pad description. The D-pad now selects where the KFS gripper is in the operator frame:

```text
D-pad up:    KFS gripper faces operator-frame front, view=0
D-pad right: KFS gripper faces operator-frame right, view=1
D-pad down:  KFS gripper faces operator-frame back / toward operator, view=2
D-pad left:  KFS gripper faces operator-frame left, view=3
```

The startup default is `view=2` because the current match setup starts with the KFS gripper facing the operator. The current physical relation is: when E-stop/body-front points operator-frame front, the KFS gripper points operator-frame left. Internally, `joystick_bridge` converts with `E-stop view = (KFS view + 1) % 4` before publishing `/local_driving`.

Left-stick neutral is still required before changing view. Right-stick rotation, chassis speed limits, acceleration limits, and watchdog behavior are unchanged.


## 2026-06-19 Current KFS-Gripper Front-Marker Control

This section supersedes the same-day `KFS view + 1` conversion note. The KFS gripper is now treated as the visible body-front marker:

```text
D-pad up:    KFS gripper / body front faces operator-frame front, view=0
D-pad right: KFS gripper / body front faces operator-frame right, view=1
D-pad down:  KFS gripper / body front faces operator-frame back / toward operator, view=2
D-pad left:  KFS gripper / body front faces operator-frame left, view=3
```

`joystick_bridge` now uses `body_front_view = KFS view` with no additional offset. Startup default remains `view=2` because the current match setup starts with the KFS gripper facing the operator. Left-stick neutral is still required before changing view; chassis limits and watchdog behavior are unchanged.


## 2026-06-19 KFS Front-Marker Startup Default

This section supersedes the same-day note that used startup `view=2`. Startup default is now `view=0`, equivalent to D-pad up, meaning the KFS gripper / body front is assumed to face operator-frame front when `joystick_bridge` starts.

The KFS gripper is still the visible body-front marker, so `body_front_view = KFS view` remains unchanged. Chassis limits, right-stick rotation, and watchdog behavior are unchanged.


## 2026-06-19 KFS Front-Marker 90-Degree Calibration

This section supersedes the same-day front-marker formula. Real-machine testing showed D-pad left was previously required to make left-stick-forward move forward when the KFS gripper was visually at the front. The active conversion is now:

```text
body_front_view = (KFS view - 1) % 4
```

D-pad semantics and startup default are unchanged: startup `view=0` means KFS gripper / visual front is assumed to face operator-frame front. Chassis limits and watchdog behavior are unchanged.
