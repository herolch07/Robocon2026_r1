> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

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

- Motor 1-4: four-wheel omni base in VEL mode
- Motor 5: KFS elevator actuator in VEL mode
- Motor 6: KFS horizontal actuator in VEL mode
- Motor 7: STAFF gripper position motor in POS_VEL mode
- Motor 8: STAFF gripper position motor in POS_VEL mode
- Arduino five-relay pneumatic panel: KFS gripper, M7/M8 staff grippers, M7/M8 inclination/head relays
- 8BitDo controller input through Linux `evdev`
- Optional keyboard teleoperation package for legacy low-speed debugging only; current match operation uses the controller

## Controller Mapping

```text
Always active:
  Left stick: base translation in operator frame
  Right stick: base in-place rotation
  D-pad: set KFS visual front direction in operator frame
  X + Y + B + A held 5 s: Raspberry Pi shutdown command

Mode select:
  SELECT / center-left: STAFF mode (/operation_mode = 1)
  START / center-right: KFS mode (/operation_mode = 2)

STAFF mode:
  A: Motor7 90° / preset cycle
  X: Motor8 90° / preset cycle
  B: Motor7 staff gripper relay toggle
  Y: Motor8 staff gripper relay toggle
  R1/R2: Motor7 trim negative/positive
  L1/L2: Motor8 trim negative/positive
  R3/P1: Motor7 inclination/head relay toggle
  L3/P2: Motor8 inclination/head relay toggle

KFS mode:
  Y: KFS gripper toggle
  L2/R2: Motor6 horizontal positive(out)/negative(in)
  L1/R1: Motor5 elevator negative(down)/positive(up)
```

## Important Current Defaults

```text
Joystick axis range: -512 .. 512
Trigger range: 0 .. 512
Joystick deadzone: 15
joystick_bridge max_speed_cm: 150.0
joystick_bridge max_rotation: 3.0
joystick_bridge translation_linear_weight: 0.1
joystick_bridge rotation_linear_weight: 0.1
local_navigation_node max_wheel_speed_rad_s: 40.0
local_navigation_node max_wheel_accel_rad_s2: 25.0
local_navigation_node accel_limit_mode: per_wheel
damiao_node motor_ids: [1,2,3,4,5,6,7,8]
damiao_node position_mode_motor_ids: [7,8]
damiao_node command_timeout_sec: 0.5
Motor7/Motor8 position presets: [0.0, 32.0, -32.0] rad
STAFF pneumatic safe_state: [1,0,1,0]
Arduino five-relay safe_state: [0,1,0,1,0]
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
src/r1_arm_control            Motor 5/6 velocity plus Motor 7/8 POS_VEL controllers and bridges
src/kfs_staff_gripper         Five-relay Arduino aggregator for KFS and STAFF pneumatic commands
src/arduino_pneumatic_driver  Arduino relay pneumatic gripper joystick bridge
src/keyboard_teleop           keyboard debugging teleoperation
```

## Safety Layers

The current control chain contains multiple watchdogs:

- `joystick_bridge`: publishes `/local_driving = [0, 0, 0]` if `/joystick_data` times out.
- `local_navigation_node`: sends zero speed to Motor 1-4 if `/local_driving` times out.
- `damiao_node`: sends zero velocity to timed-out motors for continuous VEL commands.
- `r1_arm_control` controllers: zero their actuator speed when command topics time out.
- `arduino_pneumatic_driver`: STAFF bridge returns `/pneumatic_gripper_cmd` to `[1,0,1,0]` on joystick timeout; `kfs_staff_gripper_arduino_node` owns the Arduino serial path and applies full five-relay `safe_state = [0,1,0,1,0]` on startup/reconnect/shutdown.

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

The motor driver now detects stale/disabled Motor 1-8 feedback, retries `VEL + enable + zero` every 2 seconds, and blocks non-zero commands until enabled feedback is confirmed and the controller returns to neutral. Monitor `/damiao_motor_status`; state codes are `0=RECOVERING`, `1=WAIT_NEUTRAL`, `2=READY`, `3=DISABLED`.


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

Current use of that remap is STAFF head/inclination relay control, not Motor6 horizontal:

```text
P1 -> R3 -> STAFF mode Motor7 inclination/head relay
P2 -> L3 -> STAFF mode Motor8 inclination/head relay
Motor6 horizontal -> KFS mode L2/R2, up to +/-30 rad/s
```

No ROS message, topic, node, timeout, or controller logic changed for this mapping.

## 2026-06-18 Historical Seven-Relay Operation Update（superseded）

This section records the temporary seven-relay / six-value `/pneumatic_gripper_cmd` design from 2026-06-18. It is no longer the current source-truth runtime. Current runtime uses the five-relay Arduino panel:

```text
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
/kfs_staff_gripper_cmd = [KFS gripper]
```

The controller-side P1/P2 remap remains valid: `P1=R3` and `P2=L3`, currently used in STAFF mode for Motor7/Motor8 inclination/head relays. Controller-gated autostart also remains valid: `systemd/r1-control-autostart.service` can start `scripts/wait_and_start_robot.sh`, which starts `r1_start_base_1_0.sh` after an 8BitDo / Xbox controller is active.

## 2026-06-19 Final STAFF Gripper / 90-Degree Split

This section supersedes any same-day text that says Y/A also toggle gripper relays.

Current STAFF mode split:

```text
Y  -> Motor7 left-right 90-degree / preset cycle only
A  -> Motor8 left-right 90-degree / preset cycle only
B  -> Motor7 staff gripper relay toggle only
X  -> Motor8 staff gripper relay toggle only
R1 -> Motor7 manual trim negative
R2 -> Motor7 manual trim positive
L1 -> Motor8 manual trim negative
L2 -> Motor8 manual trim positive
R3 -> Motor7 head / inclination relay toggle
L3 -> Motor8 head / inclination relay toggle
```

Current KFS mode remains:

```text
Y  -> KFS gripper toggle
L2 -> Motor6 horizontal positive / out
R2 -> Motor6 horizontal negative / in
L1 -> Motor5 elevator negative / down
R1 -> Motor5 elevator positive / up
```


## 2026-06-19 Final STAFF ABXY Layout

最新 STAFF mode ABXY：

```text
A -> Motor7 左右 90° / preset cycle only
X -> Motor8 左右 90° / preset cycle only
B -> Motor7 staff gripper relay toggle only
Y -> Motor8 staff gripper relay toggle only
```

其他 STAFF 鍵位不變：`R1/R2=Motor7 微調`，`L1/L2=Motor8 微調`，`R3=Motor7 抬頭`，`L3=Motor8 抬頭`。

KFS mode 不變：`Y=KFS gripper`，`L2/R2=horizontal positive/negative`，`L1/R1=elevator negative/positive`。


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。

## 2026-06-20 KFS mechanism speed parameters

目前 source code 中 KFS mode 的機構速度如下：

```text
Motor5 elevator = 28.0 rad/s
  L1: negative/down
  R1: positive/up

Motor6 horizontal = 30.0 rad/s
  L2: positive/out at full trigger
  R2: negative/in at full trigger
```

對應參數：`elevator_joystick_bridge_node.command_speed_rad_s=28.0`、`elevator_controller_node.max_speed_rad_s=28.0`、`horizontal_joystick_bridge_node.command_speed_rad_s=30.0`、`horizontal_controller_node.max_speed_rad_s=30.0`。只有 `/operation_mode=2` 時生效；超時保護仍為 `timeout_sec=0.3 s`。

## 2026-06-20 STAFF D-pad Down Motor7/Motor8 Swap

目前 STAFF mode 會讀取 `/view_orientation`。規則：

```text
/view_orientation = 0  # D-pad 上，KFS visual front 在機手前方
  STAFF mapping 保持正常：Motor7 按鍵仍控制 Motor7，Motor8 按鍵仍控制 Motor8

/view_orientation = 2  # D-pad 下，KFS visual front 在機手後方
  STAFF mapping 對調：所有 Motor7 staff gripper 控制改送 Motor8，所有 Motor8 staff gripper 控制改送 Motor7
```

D-pad 左/右 (`1/3`) 目前不觸發對調，保持正常 mapping。對調只在 STAFF mode (`/operation_mode=1`) 影響 staff gripper 相關控制；KFS mode、底盤左/右搖桿、Motor5 elevator、Motor6 horizontal 不受影響。

正常 mapping：

```text
A -> Motor7 90° / preset
X -> Motor8 90° / preset
B -> Motor7 staff gripper relay
Y -> Motor8 staff gripper relay
R1/R2 -> Motor7 trim -/+
L1/L2 -> Motor8 trim -/+
R3/P1 -> Motor7 inclination/head relay
L3/P2 -> Motor8 inclination/head relay
```

D-pad 下 swap mapping：

```text
A -> Motor8 90° / preset
X -> Motor7 90° / preset
B -> Motor8 staff gripper relay
Y -> Motor7 staff gripper relay
R1/R2 -> Motor8 trim +/-   # R1/R2 also swapped, so R1 positive and R2 negative
L1/L2 -> Motor7 trim +/-   # L1/L2 also swapped, so L1 positive and L2 negative
R3/P1 -> Motor8 inclination/head relay
L3/P2 -> Motor7 inclination/head relay
```

相關參數：

```text
motor_position_selector_joystick_bridge_node.swap_staff_grippers_on_view_down = true
pneumatic_gripper_joystick_bridge_node.swap_staff_grippers_on_view_down = true
```

## 2026-06-20 Chassis Rotation Speed

Right stick rotation speed default is now:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

The rotation curve remains:

```text
rotation = (0.1x + 0.9x^3) * max_rotation
```

So small right-stick input still gives fine control, while full right-stick input can request up to `3.0 rad/s`. Actual chassis motion may still be scaled by `local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s` when translation and rotation are combined.

### 2026-06-20 STAFF D-pad Down Trim Direction Update

D-pad 下的 STAFF swap 現在也會把微調方向一起對調：`R1/R2` 互換、`L1/L2` 互換。因此 D-pad 下時：

```text
R1 -> Motor8 trim positive
R2 -> Motor8 trim negative
L1 -> Motor7 trim positive
L2 -> Motor7 trim negative
```

D-pad 上仍保持原本：`R1/R2=Motor7 -/+`，`L1/L2=Motor8 -/+`。

## 2026-06-20 Archived Previous README Content - root-2026-06-18

以下內容是本次 source-verified 文檔同步前已存在的 README 段落。它們已被前面的 current/source-verified 段落取代，只保留作版本回溯與排錯依據，不代表目前實機操作。

<details><summary>Archived section 1</summary>

## 2026-06-18 Current Operation Update

This section is the latest operation summary. It supersedes older sections that describe the previous P1/P2 direction, relay7 as reserved, or manual startup as the only startup flow. Older sections remain for traceability.

```text
P1 = R3 -> STAFF mode Motor7 inclination/head relay
P2 = L3 -> STAFF mode Motor8 inclination/head relay
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


## 2026-06-19 STAFF/KFS Operation Mode Keymap

The current mechanism keymap uses direct operation modes instead of a third Zone 3 mode:

```text
SELECT / middle-left = STAFF mode
START  / middle-right = KFS mode
```

Chassis control is not mode-gated: left stick, right stick, and D-pad KFS visual-front selection stay active in all modes.

STAFF mode:

```text
X  -> Motor8 staff gripper preset/open-close cycle
B  -> Motor7 staff gripper preset/open-close cycle
L2 -> Motor8 manual trim
R2 -> Motor7 manual trim
L1 -> Motor8 head/inclination toggle
R1 -> Motor7 head/inclination toggle
Y  -> Motor8 height toggle
A  -> Motor7 height toggle
```

KFS mode:

```text
Y -> KFS gripper toggle
```

`/operation_mode` publishes `0=INVALID, 1=STAFF, 2=KFS`. Mode switching does not command actuators by itself; it only changes which bridge accepts later button presses.


## 2026-06-19 KFS Mode Zone2 Expansion

KFS mode now controls more than the KFS gripper:

```text
Y  -> KFS gripper toggle
L2 -> Motor6 horizontal negative/in
R2 -> Motor6 horizontal positive/out
L1 -> Motor5 elevator negative/down
R1 -> Motor5 elevator positive/up
```

The same L1/R1/L2/R2 buttons are mode-gated: STAFF mode routes them to staff head toggles and Motor7/8 trim; KFS mode routes them to elevator/horizontal. Chassis sticks and D-pad remain mode-independent.


## 2026-06-19 Five-Relay Pneumatic Panel

The current Arduino relay panel now has five relays on pins `22,24,25,27,28` and accepts `[r1,r2,r3,r4,r5]`.

ROS relay order:

```text
[KFS gripper, M7 staff gripper, M8 inclination, M8 staff gripper, M7 inclination]
```

Motor7/Motor8 height relays were removed. STAFF mode no longer uses A/Y for height. X/B now toggle the corresponding staff gripper relay and still feed the Motor8/Motor7 position preset bridge.


## 2026-06-19 STAFF/KFS Keymap Correction

Current STAFF mode keymap supersedes the earlier X/B mapping:

```text
Y  -> Motor7 left-right 90-degree preset cycle + Motor7 gripper relay
A  -> Motor8 left-right 90-degree preset cycle + Motor8 gripper relay
R1 -> Motor7 trim negative
R2 -> Motor7 trim positive
L1 -> Motor8 trim negative
L2 -> Motor8 trim positive
B/X -> not used by STAFF mode
```

KFS mode horizontal was swapped:

```text
L2 -> Motor6 horizontal positive/out
R2 -> Motor6 horizontal negative/in
```


## 2026-06-19 STAFF Head Relay on L3/R3

STAFF mode now uses stick-click buttons for head/inclination relays:

```text
L3 -> Motor8 inclination/head relay
R3 -> Motor7 inclination/head relay
```

L1/R1/L2/R2 remain reserved for Motor7/8 manual trim.

</details>

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
