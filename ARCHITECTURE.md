> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# R1 ROS 2 System Architecture

本文记录当前 R1 工作区的整体架构、node/topic 数据流和各 package 职责。

## 1. Workspace Overview

```text
r1_control_ws/
  src/
    my_joystick_msgs
    my_joystick_driver
    joystick_bridge
    base_omniwheel_r2_700
    r1_arm_control
    arduino_pneumatic_driver
    keyboard_teleop
```

当前 R1 系统由三条主要控制链组成：

```text
1. 底盘控制链
2. Motor 5/6/7/8 機構執行控制鏈
3. Arduino pneumatic gripper 控制链
```

另外有一条可选键盘调试链：

```text
keyboard_teleop -> existing command topics
```

## 2. Architecture Graphs

### Full System Overview（source-verified current）

```mermaid
flowchart TD
    Controller[8BitDo Controller]
    JoyNode["/joystick_node"]
    JoyTopic["/joystick_data"]

    ModeNode["/operation_mode_selector_node<br/>SELECT=STAFF / START=KFS"]
    ModeTopic["/operation_mode<br/>0 invalid / 1 STAFF / 2 KFS"]

    BaseBridge["/joystick_bridge<br/>left/right stick + D-pad view"]
    ViewTopic["/view_orientation<br/>0 front / 1 right / 2 back / 3 left"]
    LocalDriving["/local_driving<br/>[direction, cm/s, rad/s]"]
    NavNode["/local_navigation_node"]

    ElevatorBridge["/elevator_joystick_bridge_node<br/>KFS L1/R1"]
    ElevatorCtrl["/elevator_controller_node<br/>Motor5 VEL"]
    HorizontalBridge["/horizontal_joystick_bridge_node<br/>KFS L2/R2"]
    HorizontalCtrl["/horizontal_controller_node<br/>Motor6 VEL"]

    PosBridge["/motor_position_selector_joystick_bridge_node<br/>STAFF A/X + R1/R2 + L1/L2"]
    M7Pos["/motor7_position_controller_node<br/>Motor7 POS_VEL"]
    M8Pos["/motor8_position_controller_node<br/>Motor8 POS_VEL"]

    StaffPneu["/pneumatic_gripper_joystick_bridge_node<br/>STAFF B/Y/R3/L3"]
    StaffCmd["/pneumatic_gripper_cmd<br/>[M7 grip, M8 head, M8 grip, M7 head]"]
    KfsPneu["/kfs_staff_gripper_joystick_bridge_node<br/>KFS Y"]
    KfsCmd["/kfs_staff_gripper_cmd<br/>[KFS gripper]"]
    Arduino["/kfs_staff_gripper_arduino_node<br/>five-relay serial owner"]

    Power["/joystick_shutdown_node<br/>X+Y+B+A hold 5s"]
    DamiaoCmd["/damiao_control"]
    Damiao["/motor_controller_node<br/>damiao_node"]
    Motors["Motor 1-8<br/>M1-6 VEL, M7-8 POS_VEL"]

    Controller --> JoyNode --> JoyTopic
    JoyTopic --> ModeNode --> ModeTopic
    JoyTopic --> BaseBridge --> LocalDriving --> NavNode --> DamiaoCmd --> Damiao --> Motors
    BaseBridge --> ViewTopic

    JoyTopic --> ElevatorBridge --> ElevatorCtrl --> DamiaoCmd
    ModeTopic --> ElevatorBridge
    JoyTopic --> HorizontalBridge --> HorizontalCtrl --> DamiaoCmd
    ModeTopic --> HorizontalBridge

    JoyTopic --> PosBridge
    ModeTopic --> PosBridge
    ViewTopic --> PosBridge
    PosBridge --> M7Pos --> DamiaoCmd
    PosBridge --> M8Pos --> DamiaoCmd

    JoyTopic --> StaffPneu
    ModeTopic --> StaffPneu
    ViewTopic --> StaffPneu
    StaffPneu --> StaffCmd --> Arduino

    JoyTopic --> KfsPneu
    ModeTopic --> KfsPneu
    KfsPneu --> KfsCmd --> Arduino

    JoyTopic --> Power
```

### Base Chassis Chain

```mermaid
flowchart LR
    Controller[8BitDo Controller]
    JoyNode["/joystick_node"]
    JoyTopic["/joystick_data"]
    Bridge["/joystick_bridge<br/>max_speed=150cm/s<br/>max_rotation=3.0rad/s"]
    LocalDriving["/local_driving"]
    Nav["/local_navigation_node<br/>40rad/s wheel limit<br/>25rad/s² accel<br/>per_wheel default"]
    DamiaoCmd["/damiao_control"]
    Driver["/motor_controller_node"]
    Motors["Motor 1-4 chassis"]

    Controller --> JoyNode --> JoyTopic --> Bridge --> LocalDriving --> Nav --> DamiaoCmd --> Driver --> Motors
```

### Mechanism Motor Chain

```mermaid
flowchart TD
    Joy["/joystick_data"]
    Mode["/operation_mode"]
    View["/view_orientation"]
    Damiao["/damiao_control"]

    EB["/elevator_joystick_bridge_node<br/>KFS L1/R1"]
    EC["/elevator_controller_node<br/>Motor5 VEL 28rad/s"]
    HB["/horizontal_joystick_bridge_node<br/>KFS L2/R2"]
    HC["/horizontal_controller_node<br/>Motor6 VEL 30rad/s"]
    PB["/motor_position_selector_joystick_bridge_node<br/>STAFF A/X/R1/R2/L1/L2"]
    M7I["/motor7_position_input"]
    M8I["/motor8_position_input"]
    M7["/motor7_position_controller_node<br/>0,+32,-32rad"]
    M8["/motor8_position_controller_node<br/>0,+32,-32rad"]

    Joy --> EB --> EC --> Damiao
    Mode --> EB
    Joy --> HB --> HC --> Damiao
    Mode --> HB
    Joy --> PB
    Mode --> PB
    View --> PB
    PB --> M7I --> M7 --> Damiao
    PB --> M8I --> M8 --> Damiao
```

### Pneumatic / Arduino Five-Relay Chain

```mermaid
flowchart LR
    Joy["/joystick_data"]
    Mode["/operation_mode"]
    View["/view_orientation"]
    StaffBridge["/pneumatic_gripper_joystick_bridge_node<br/>STAFF B/Y/R3/L3"]
    StaffCmd["/pneumatic_gripper_cmd<br/>[M7 grip, M8 head, M8 grip, M7 head]"]
    KfsBridge["/kfs_staff_gripper_joystick_bridge_node<br/>KFS Y"]
    KfsCmd["/kfs_staff_gripper_cmd<br/>[KFS gripper]"]
    ArduinoNode["/kfs_staff_gripper_arduino_node"]
    Relay["Arduino pins 22,24,25,27,28<br/>[KFS, M7 grip, M8 head, M8 grip, M7 head]"]

    Joy --> StaffBridge
    Mode --> StaffBridge
    View --> StaffBridge
    StaffBridge --> StaffCmd --> ArduinoNode
    Joy --> KfsBridge
    Mode --> KfsBridge
    KfsBridge --> KfsCmd --> ArduinoNode --> Relay
```

### Safety Watchdog Chain

```mermaid
flowchart TD
    JoyTimeout["/joystick_bridge<br/>/joystick_data timeout 0.3s"] --> LocalStop["/local_driving=[0,0,0]"]
    LocalTimeout["/local_navigation_node<br/>/local_driving timeout 0.3s"] --> WheelStop["Motor1-4 speed=0"]
    DamiaoTimeout["/motor_controller_node<br/>command timeout 0.5s"] --> DamiaoSafe["VEL: 0rad/s<br/>POS_VEL: hold feedback position"]
    ArmTimeout["r1_arm_control<br/>input/command timeout"] --> ArmSafe["Motor5/6 stop<br/>Motor7/8 stop trim / hold"]
    PneuTimeout["STAFF/KFS relay bridges + aggregator"] --> RelaySafe["STAFF [1,0,1,0]<br/>full [0,1,0,1,0]"]
```

## 3. Full Controller Runtime

当前推荐启动脚本：

```bash
./r1_start_base_1_0.sh
```

该脚本启动 tmux session：

```text
r1_control
```

tmux 窗口（以 `r1_start_base_1_0.sh` 为 source truth）：

```text
0 joystick        my_joystick_driver/joystick_node
1 op_mode         operation_mode_control/operation_mode_selector_node
2 base_bridge     joystick_bridge/joystick_bridge
3 motors          base_omniwheel_r2_700/damiao_node
4 nav             base_omniwheel_r2_700/local_navigation_node
5 elevator        r1_arm_control/elevator_controller_node
6 elev_bridge     r1_arm_control/elevator_joystick_bridge_node
7 horizontal      r1_arm_control/horizontal_controller_node
8 horiz_bridge    r1_arm_control/horizontal_joystick_bridge_node
9 motor7_pos      r1_arm_control/motor7_position_controller_node
10 motor8_pos     r1_arm_control/motor8_position_controller_node
11 motor_select   r1_arm_control/motor_position_selector_joystick_bridge_node
12 relay_panel    kfs_staff_gripper/kfs_staff_gripper_arduino_node
13 pneu_bridge    arduino_pneumatic_driver/pneumatic_gripper_joystick_bridge_node
14 kfs_bridge     kfs_staff_gripper/kfs_staff_gripper_joystick_bridge_node
15 power_shutdown robot_power_control/joystick_shutdown_node dry_run=false
16 monitor        debug shell
```

旧 `arm_gripper_controller_node`、`arm_gripper_joystick_bridge_node`、`pneumatic_relay_driver_node` 不在当前启动脚本中。

## 4. Joystick Input Layer

Package:

```text
src/my_joystick_driver
```

Node:

```text
/joystick_node
```

Hardware input:

```text
8BitDo controller
Linux evdev
/dev/input/event*
```

Published topic:

```text
/joystick_data
type: my_joystick_msgs/msg/Joystick
rate: 20 Hz
```

Current message range:

```text
lx/ly/rx/ry: -512 .. 512
dx/dy: -512, 0, 512
l2/r2: 0 .. 512
buttons: bool
```

Custom message package:

```text
src/my_joystick_msgs
```

Message:

```text
my_joystick_msgs/msg/Joystick
```

## 5. Base Chassis Control Chain

Packages:

```text
src/joystick_bridge
src/base_omniwheel_r2_700
```

Data flow:

```text
8BitDo controller
  -> /joystick_node
  -> /joystick_data
  -> /joystick_bridge
  -> /local_driving
  -> /local_navigation_node
  -> /damiao_control
  -> /motor_controller_node
  -> USB-CAN
  -> DM Motor 1-4
```

Detailed flow:

```text
/joystick_node
  publishes /joystick_data
    type: my_joystick_msgs/msg/Joystick

/joystick_bridge
  subscribes /joystick_data
  converts left/right stick to chassis command
  publishes /local_driving
    type: std_msgs/msg/Float32MultiArray
    data = [direction_rad, speed_cm_per_sec, rotation_rad_per_sec]

/local_navigation_node
  subscribes /local_driving
  computes four-wheel omni inverse kinematics
  publishes /damiao_control
    type: std_msgs/msg/Float32MultiArray
    data = [motor_id, mode, speed_rad_s, duration]

/motor_controller_node
  implemented by damiao_node.py
  subscribes /damiao_control
  sends velocity commands through USB-CAN
  controls Motor 1-4 for chassis
```

Base motor mapping:

```text
Motor 1 = left front
Motor 2 = right front
Motor 3 = right rear
Motor 4 = left rear
```

Current base kinematics defaults:

```text
lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4 = [1, 1, -1, -1]
lateral_coeff_1..4 = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

## 6. Arm Actuator Control Chain

Package:

```text
src/r1_arm_control
```

Controlled actuators:

```text
Motor 5 = elevator, VEL mode, KFS mode only
Motor 6 = horizontal movement, VEL mode, KFS mode only
Motor 7 = staff gripper position motor, POS_VEL mode, STAFF mode only
Motor 8 = staff gripper position motor, POS_VEL mode, STAFF mode only
```

### Motor 5 Elevator

```text
/joystick_data + /operation_mode
  -> /elevator_joystick_bridge_node
  -> /elevator_speed_cmd [speed_rad_s]
  -> /elevator_controller_node
  -> /damiao_control
  -> /motor_controller_node
  -> Motor 5
```

Current mapping: KFS mode `L1 = negative/down`，`R1 = positive/up`，default speed `28.0 rad/s`。

### Motor 6 Horizontal

```text
/joystick_data + /operation_mode
  -> /horizontal_joystick_bridge_node
  -> /horizontal_speed_cmd [speed_rad_s]
  -> /horizontal_controller_node
  -> /damiao_control
  -> /motor_controller_node
  -> Motor 6
```

Current mapping: KFS mode `L2 = positive/out`，`R2 = negative/in`，default speed `30.0 rad/s`。

### Motor 7 / Motor 8 Staff Position Motors

```text
/joystick_data + /operation_mode + /view_orientation
  -> /motor_position_selector_joystick_bridge_node
  -> /motor7_position_input / /motor8_position_input
  -> /motor7_position_controller_node / /motor8_position_controller_node
  -> /damiao_control mode=2 POS_VEL
  -> /motor_controller_node
  -> Motor 7 / Motor 8
```

Input topic format:

```text
/tmotor_position_input = [toggle_event, trim_input, valid]
```

Current defaults for both Motor7 and Motor8:

```text
position_a_rad = 0.0
position_b_rad = 32.0
position_c_rad = -32.0
min_position_rad = -32.0
max_position_rad = 32.0
preset_speed_rad_s = 3.0
trim_speed_rad_s = 2.0
```

Normal STAFF mapping: `A=Motor7 preset`，`X=Motor8 preset`，`R1/R2=Motor7 trim -/+`，`L1/L2=Motor8 trim -/+`。當 `/view_orientation=2`（D-pad 下）時，Motor7/Motor8 控制與 trim 方向按 source code 對調。

## 7. Pneumatic Gripper Control Chain

Packages:

```text
src/arduino_pneumatic_driver
src/kfs_staff_gripper
```

Current hardware:

```text
Arduino Mega
5-channel relay / solenoid valve panel
pins = 22, 24, 25, 27, 28
HIGH = ON, LOW = OFF
```

Current relay order:

```text
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
full safe_state = [0,1,0,1,0]
```

Data flow:

```text
STAFF: /joystick_data + /operation_mode + /view_orientation
  -> /pneumatic_gripper_joystick_bridge_node
  -> /pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
  -> /kfs_staff_gripper_arduino_node

KFS: /joystick_data + /operation_mode
  -> /kfs_staff_gripper_joystick_bridge_node
  -> /kfs_staff_gripper_cmd = [KFS gripper]
  -> /kfs_staff_gripper_arduino_node
```

`kfs_staff_gripper_arduino_node` 是当前唯一 Arduino serial owner。不要同时启动旧 `pneumatic_relay_driver_node`。

## 8. Keyboard Teleop Debug Chain

Package:

```text
src/keyboard_teleop
```

Node:

```text
/keyboard_teleop_node
```

Purpose:

```text
Temporary low-speed debugging without a physical controller.
```

Source truth: `keyboard_teleop_node` 仍发布旧调试 topic，包括 `/arm_gripper_speed_cmd` 和旧二值 `/pneumatic_gripper_cmd`。因此它不适用于当前五路 Arduino relay 比赛操作，也不应和 joystick bridges 同时运行。

```text
Do not run keyboard_teleop together with joystick bridges.
Do not use keyboard_teleop for current pneumatic competition operation.
```

## 9. Safety Architecture

### Joystick Bridge Watchdog

```text
/joystick_bridge
  watches /joystick_data
  if timeout > input_timeout_sec = 0.3 s
  publishes /local_driving = [0, 0, 0]
```

### Base Navigation Watchdog

```text
/local_navigation_node
  watches /local_driving
  if timeout > command_timeout_sec = 0.3 s
  publishes zero speed to Motor 1-4 through /damiao_control
```

### Damiao Motor Watchdog

```text
/motor_controller_node
  watches command age per motor_id
  VEL motors timeout > command_timeout_sec = 0.5 s -> 0 rad/s
  POS_VEL Motor7/8 timeout -> hold latest feedback position
```

### Arm Controllers Watchdog

```text
/elevator_controller_node and /horizontal_controller_node
  watch speed command topics
  if timeout > timeout_sec = 0.3 s
  publish 0 rad/s to /damiao_control

/motor7_position_controller_node and /motor8_position_controller_node
  watch position input and feedback freshness
  invalid input stops trim/toggle; feedback timeout prevents trusting stale position
```

### Pneumatic Driver Watchdog

```text
/pneumatic_gripper_joystick_bridge_node
  if joystick timeout > input_timeout_sec = 0.3 s
  publishes STAFF safe_state = [1,0,1,0]

/kfs_staff_gripper_joystick_bridge_node
  if joystick timeout > input_timeout_sec = 0.3 s
  publishes KFS safe_state = [0]

/kfs_staff_gripper_arduino_node
  owns the Arduino serial port and aggregates /pneumatic_gripper_cmd + /kfs_staff_gripper_cmd
  if one command source timeout > command_timeout_sec = 0.5 s
  restores only that source's relay group from full safe_state = [0,1,0,1,0]
```

## 10. Topic Summary

| Topic | Type | Publisher | Subscriber |
|---|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | `/joystick_node` | joystick / mode / mechanism / power bridge nodes |
| `/operation_mode` | `std_msgs/msg/Int32` | `/operation_mode_selector_node` | mechanism bridge nodes |
| `/view_orientation` | `std_msgs/msg/Int32` | `/joystick_bridge` | STAFF position/pneumatic bridge nodes |
| `/local_driving` | `std_msgs/msg/Float32MultiArray` | `/joystick_bridge`, optional legacy `/keyboard_teleop_node` | `/local_navigation_node` |
| `/damiao_control` | `std_msgs/msg/Float32MultiArray` | base/arm controllers | `/motor_controller_node` |
| `/damiao_motor_status` | `std_msgs/msg/Float32MultiArray` | `/motor_controller_node` | monitor / debug terminal |
| `/elevator_speed_cmd` | `std_msgs/msg/Float32MultiArray` | `/elevator_joystick_bridge_node`, optional keyboard | `/elevator_controller_node` |
| `/horizontal_speed_cmd` | `std_msgs/msg/Float32MultiArray` | `/horizontal_joystick_bridge_node`, optional keyboard | `/horizontal_controller_node` |
| `/elevator_status` | `std_msgs/msg/Float32MultiArray` | `/elevator_controller_node` | monitor |
| `/horizontal_status` | `std_msgs/msg/Float32MultiArray` | `/horizontal_controller_node` | monitor |
| `/motor7_position_input` | `std_msgs/msg/Float32MultiArray` | `/motor_position_selector_joystick_bridge_node` | `/motor7_position_controller_node` |
| `/motor8_position_input` | `std_msgs/msg/Float32MultiArray` | `/motor_position_selector_joystick_bridge_node` | `/motor8_position_controller_node` |
| `/motor7_position_status` | `std_msgs/msg/Float32MultiArray` | `/motor7_position_controller_node` | monitor |
| `/motor8_position_status` | `std_msgs/msg/Float32MultiArray` | `/motor8_position_controller_node` | monitor |
| `/motor_position_selector_status` | `std_msgs/msg/Float32MultiArray` | `/motor_position_selector_joystick_bridge_node` | monitor |
| `/pneumatic_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | `/pneumatic_gripper_joystick_bridge_node` | `/kfs_staff_gripper_arduino_node` |
| `/kfs_staff_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | `/kfs_staff_gripper_joystick_bridge_node` | `/kfs_staff_gripper_arduino_node` |
| `/kfs_staff_gripper_status` | `std_msgs/msg/String` | `/kfs_staff_gripper_arduino_node` | monitor |
| `/robot_power_status` | `std_msgs/msg/String` | `/joystick_shutdown_node` | monitor |

## 11. Current Important Defaults

```text
Joystick axis range: -512 .. 512
Joystick trigger range: 0 .. 512
Joystick deadzone: 15

joystick_bridge:
  max_speed_cm = 150.0
  translation_linear_weight = 0.1
  max_rotation = 3.0
  rotation_linear_weight = 0.1
  input_timeout_sec = 0.3

local_navigation_node:
  max_wheel_speed_rad_s = 40.0
  max_wheel_accel_rad_s2 = 25.0
  accel_limit_mode = per_wheel
  command_timeout_sec = 0.3
  omniwheel_radius_m = 0.0635

damiao_node / motor_controller_node:
  motor_ids = [1,2,3,4,5,6,7,8]
  position_mode_motor_ids = [7,8]
  command_timeout_sec = 0.5

r1_arm_control Motor7/Motor8 POS_VEL:
  position_a_rad = 0.0
  position_b_rad = 32.0
  position_c_rad = -32.0
  min_position_rad = -32.0
  max_position_rad = 32.0
  preset_speed_rad_s = 3.0
  trim_speed_rad_s = 2.0

Arduino five-relay panel:
  /pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
  /kfs_staff_gripper_cmd = [KFS gripper]
  full safe_state = [0,1,0,1,0]
```

## ROS2 Domain Boundary

R1 control graph must run inside its own ROS2 domain:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

R2 should use a different domain, for example `ROS_DOMAIN_ID=2`. This prevents R1 from discovering R2-only nodes such as `/damiao_motor_controller` and topics such as `/base/dummy_control`. See `ROS_DOMAIN_ISOLATION.md`.

## 2026-06-06 Joystick Bridge 更新

左摇杆平移链路使用 `150 cm/s` 上限，右摇杆旋转链路使用 `3.0 rad/s` 上限；两者均采用 `0.1x + 0.9x³`。Motor 7 的 R2/L2 净输入同样采用该曲线，最大 `1.3 rad/s`。START/SELECT 不参与底盘调速，watchdog 接口不变。

## 2026-06-07 Damiao 急停恢复状态机

```mermaid
stateDiagram-v2
    [*] --> RECOVERING
    READY --> RECOVERING: feedback timeout / isEnable=false
    RECOVERING --> RECOVERING: every 2s VEL + enable + zero
    RECOVERING --> WAIT_NEUTRAL: fresh enabled feedback
    WAIT_NEUTRAL --> READY: zero-speed command
    WAIT_NEUTRAL --> RECOVERING: feedback lost
```

`RECOVERING` 和 `WAIT_NEUTRAL` 都只允许向硬件发送模式匹配的安全命令。`/damiao_motor_status` 发布 Motor 1-8 的状态，其中 Motor7/8 使用 POS_VEL hold-current-position 安全命令。


## 2026-06-15 人視角控制架構更新

目前底盤上層加入「操作人座標到車體座標」的離散轉換，仍保持節點解耦：

```text
/joystick_data
  -> joystick_bridge
       D-pad: 保存 E-stop 在人視角中的 0/90/180/270 度方向
       left stick: operator frame -> body frame
       right stick: rotation unchanged
  -> /local_driving
  -> local_navigation_node
```

`joystick_bridge` 另發布 `/view_orientation` (`std_msgs/msg/Int32`)：
`0=前、1=右、2=後、3=左`。視角切換預設要求左搖桿回中，沒有 IMU 自動修正。

Motor6 的目前輸入鏈為：

```text
KFS mode L2/R2 -> horizontal_joystick_bridge_node
               -> /horizontal_speed_cmd [-30..+30 rad/s]
               -> horizontal_controller_node
               -> Motor6 VEL
```

P1/P2 目前只是手柄內部 remap：`P1=R3`、`P2=L3`，在 STAFF mode 用於 Motor7/Motor8 inclination/head relay，不再控制 Motor6 horizontal。

底層運動學、CAN driver、Motor6 controller、topic 類型與 watchdog 均未改變。本功能已於
2026-06-15 完成實機驗證。

## 2026-06-18 Current Runtime Architecture Override

This section records the current runtime architecture and supersedes older node graphs that still mention legacy arm gripper or two-channel pneumatic nodes.

Startup path:

```text
scripts/wait_and_start_robot.sh                  # optional boot watcher
  -> r1_start_base_1_0.sh                         # tmux runtime launcher
```

Current tmux runtime nodes:

```text
my_joystick_driver/joystick_node
joystick_bridge/joystick_bridge
base_omniwheel_r2_700/damiao_node
base_omniwheel_r2_700/local_navigation_node
r1_arm_control/elevator_controller_node
r1_arm_control/elevator_joystick_bridge_node
r1_arm_control/horizontal_controller_node
r1_arm_control/horizontal_joystick_bridge_node
r1_arm_control/motor7_position_controller_node
r1_arm_control/motor8_position_controller_node
r1_arm_control/motor_position_selector_joystick_bridge_node
kfs_staff_gripper/kfs_staff_gripper_arduino_node
arduino_pneumatic_driver/pneumatic_gripper_joystick_bridge_node
kfs_staff_gripper/kfs_staff_gripper_joystick_bridge_node
```

Current pneumatic aggregation:

```text
pneumatic_gripper_joystick_bridge_node -> /pneumatic_gripper_cmd
kfs_staff_gripper_joystick_bridge_node -> /kfs_staff_gripper_cmd
kfs_staff_gripper_arduino_node -> Arduino [KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

Do not launch the legacy `pneumatic_relay_driver_node` together with `kfs_staff_gripper_arduino_node`, because both would try to own the Arduino serial path.


## 2026-06-19 KFS gripper 視角基準更新

本節取代 2026-06-15 中「D-pad 保存 E-stop 方向」的現行架構描述。節點拆分不變，只有 `joystick_bridge` 的視角語義改變：

```text
/joystick_data
  -> joystick_bridge
       D-pad: 保存 KFS gripper 在人視角中的 0/90/180/270 度方向
       internal: E-stop/body-front view = (KFS view + 1) % 4
       left stick: operator frame -> body frame
       right stick: rotation unchanged
  -> /local_driving
  -> local_navigation_node
```

`/view_orientation` (`std_msgs/msg/Int32`) 現在發布 KFS gripper 方向，`0=前、1=右、2=後、3=左`。預設值為 `2`，對應 KFS gripper 開機朝向操作人。底層運動學、CAN driver、Motor6 controller、topic 類型與 watchdog 均未改變。


## 2026-06-19 KFS gripper 車頭標架構更新

本節取代同日 KFS `+1` 偏移方案。節點拆分不變，只有 `joystick_bridge` 的視角換算改為 KFS gripper 直接代表車體前方：

```text
/joystick_data
  -> joystick_bridge
       D-pad: 保存 KFS gripper／body-front 在人視角中的 0/90/180/270 度方向
       internal: body_front_view = KFS view
       left stick: operator frame -> body frame
       right stick: rotation unchanged
  -> /local_driving
  -> local_navigation_node
```

`/view_orientation` (`std_msgs/msg/Int32`) 發布 KFS gripper／車頭方向，`0=前、1=右、2=後、3=左`。預設值為 `2`。底層運動學、CAN driver、Motor6 controller、topic 類型與 watchdog 均未改變。


## 2026-06-19 KFS gripper 開機預設更新

`joystick_bridge` 的節點架構不變，但 `default_view_orientation` 預設由 `2` 改為 `0`。啟動時假設 KFS gripper／body-front 在操作人視角前方。

`/view_orientation` 啟動後應發布 `0`；KFS gripper 仍直接視為車體前方，內部仍使用 `body_front_view = KFS view`。


## 2026-06-19 KFS 車頭標 90 度校正架構更新

`joystick_bridge` 節點連線不變，但根據實機結果更新 operator-frame 到 body-frame 的校正公式：

```text
body_front_view = (KFS view - 1) % 4
```

`/view_orientation` 仍表示 KFS gripper／視覺車頭在人視角中的方向，啟動預設仍為 `0`。底層 `local_navigation_node`、CAN driver、topic 類型、速度限制與 watchdog 均未改變。


## 2026-06-19 STAFF/KFS operation mode architecture

新增 `operation_mode_control` package，負責把 SELECT/START 轉換為 `/operation_mode`：

```text
/joystick_data
  -> operation_mode_selector_node
  -> /operation_mode 0=INVALID, 1=STAFF, 2=KFS
```

下游 bridge 只透過 topic 解耦，不依賴 selector 內部實作：

```text
/operation_mode=1 STAFF
  -> motor_position_selector_joystick_bridge_node 接受 A/X/R1/R2/L1/L2
  -> pneumatic_gripper_joystick_bridge_node 接受 B/Y/R3/L3

/operation_mode=2 KFS
  -> kfs_staff_gripper_joystick_bridge_node 接受 Y
  -> horizontal_joystick_bridge_node 接受 L2/R2
  -> elevator_joystick_bridge_node 接受 L1/R1
```

`joystick_bridge` 底盤控制不訂閱 `/operation_mode`，因此左搖桿、右搖桿、D-pad KFS 視角在所有 mode 中保持一致。

Timeout：`operation_mode_selector_node` 在 joystick timeout 後發布 `0`；各 mechanism bridge 在 mode timeout 或 joystick timeout 時忽略按鍵或回 safe state。


## 2026-06-19 KFS mode elevator/horizontal architecture

`elevator_joystick_bridge_node` 與 `horizontal_joystick_bridge_node` 現在也訂閱 `/operation_mode`：

```text
/operation_mode=2 KFS
  -> kfs_staff_gripper_joystick_bridge_node accepts Y
  -> horizontal_joystick_bridge_node accepts L2/R2
  -> elevator_joystick_bridge_node accepts L1/R1

/operation_mode=1 STAFF
  -> horizontal/elevator bridge publish zero
```

這避免 L1/R1/L2/R2 在 STAFF/KFS 兩套機構間互相誤觸。


## 2026-06-19 five-relay pneumatic architecture

Arduino pneumatic panel now exposes five relay outputs:

```text
relay pins: 22, 24, 25, 27, 28
serial: [KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

`kfs_staff_gripper_arduino_node` maps:

```text
/kfs_staff_gripper_cmd length 1 -> relay 1
/pneumatic_gripper_cmd length 4 -> relay 2-5
```

The removed Motor7/Motor8 height relays also remove all STAFF height actions. Current source routes A/X only to Motor7/8 POS_VEL preset cycles, and B/Y only to staff gripper relay toggles.


## 2026-06-19 STAFF/KFS keymap correction architecture

Current STAFF mode routing is source-verified as:

```text
/operation_mode=1 STAFF
  A -> Motor7 POS_VEL preset cycle only
  X -> Motor8 POS_VEL preset cycle only
  B -> Motor7 staff gripper relay toggle only
  Y -> Motor8 staff gripper relay toggle only
  R1/R2 -> Motor7 trim negative/positive
  L1/L2 -> Motor8 trim negative/positive
```

KFS horizontal trigger routing remains `L2 positive/out`, `R2 negative/in`.


## 2026-06-19 STAFF L3/R3 head relay architecture

`pneumatic_gripper_joystick_bridge_node` now maps STAFF mode L3/R3 into the five-relay panel:

```text
L3 -> /pneumatic_gripper_cmd M8 inclination index 1
R3 -> /pneumatic_gripper_cmd M7 inclination index 3
```

The L1/R1/L2/R2 trim routing remains in `motor_position_selector_joystick_bridge_node`.


## 2026-06-19 Final STAFF Gripper / 90-Degree Split

This section supersedes any same-day text that says Y/A also toggle gripper relays.

Current STAFF mode split:

```text
A  -> Motor7 left-right 90-degree / preset cycle only
X  -> Motor8 left-right 90-degree / preset cycle only
B  -> Motor7 staff gripper relay toggle only
Y  -> Motor8 staff gripper relay toggle only
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

## 2026-06-20 Current Rotation Default

Current source default:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

Older sections mentioning `1.2 rad/s` or `2.4 rad/s` are historical and are not the current runtime default.

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
