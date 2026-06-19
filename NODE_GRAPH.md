# R1 Node / Topic Graph

本文专门说明当前 R1 ROS 2 系统里各个 node 如何串联、topic 如何传递，以及每个 topic 的数据格式。

## 1. 总览图

```mermaid
flowchart TD
    Controller[8BitDo Controller]
    JoyNode["/joystick_node<br/>my_joystick_driver"]
    JoyTopic["/joystick_data<br/>my_joystick_msgs/msg/Joystick<br/>lx ly rx ry: -512..512<br/>l2 r2: 0..512<br/>buttons: bool"]

    BaseBridge["/joystick_bridge<br/>joystick_bridge"]
    LocalDriving["/local_driving<br/>std_msgs/Float32MultiArray<br/>[direction_rad, speed_cm_s, rotation_rad_s]"]
    NavNode["/local_navigation_node<br/>base_omniwheel_r2_700"]

    ElevBridge["/elevator_joystick_bridge_node"]
    ElevCmd["/elevator_speed_cmd<br/>Float32MultiArray<br/>[speed_rad_s]"]
    ElevCtrl["/elevator_controller_node"]

    HorizBridge["/horizontal_joystick_bridge_node"]
    HorizCmd["/horizontal_speed_cmd<br/>Float32MultiArray<br/>[speed_rad_s]"]
    HorizCtrl["/horizontal_controller_node"]

    ArmGripBridge["/arm_gripper_joystick_bridge_node"]
    ArmGripCmd["/arm_gripper_speed_cmd<br/>Float32MultiArray<br/>[speed_rad_s]"]
    ArmGripCtrl["/arm_gripper_controller_node"]

    PneuBridge["/pneumatic_gripper_joystick_bridge_node"]
    PneuCmd["/pneumatic_gripper_cmd<br/>Int32MultiArray<br/>[D9_gripper, D8_height]"]
    PneuDriver["/pneumatic_relay_driver_node"]
    Arduino["Arduino Mega<br/>Serial: [D9,D8]\\n"]
    Relay["Relay / Solenoid<br/>D9 gripper<br/>D8 height"]

    DamiaoCmd["/damiao_control<br/>Float32MultiArray<br/>[motor_id, mode, speed_rad_s, duration]"]
    DamiaoNode["/motor_controller_node<br/>started by damiao_node"]
    M1to4["Motor 1-4<br/>Chassis"]
    M5["Motor 5<br/>Elevator"]
    M6["Motor 6<br/>Horizontal"]
    M7["Motor 7<br/>Arm gripper motor"]

    Controller --> JoyNode --> JoyTopic

    JoyTopic --> BaseBridge --> LocalDriving --> NavNode --> DamiaoCmd

    JoyTopic --> ElevBridge --> ElevCmd --> ElevCtrl --> DamiaoCmd
    JoyTopic --> HorizBridge --> HorizCmd --> HorizCtrl --> DamiaoCmd
    JoyTopic --> ArmGripBridge --> ArmGripCmd --> ArmGripCtrl --> DamiaoCmd

    DamiaoCmd --> DamiaoNode
    DamiaoNode --> M1to4
    DamiaoNode --> M5
    DamiaoNode --> M6
    DamiaoNode --> M7

    JoyTopic --> PneuBridge --> PneuCmd --> PneuDriver --> Arduino --> Relay
```

## 2. 底盘链路

```mermaid
flowchart LR
    A["8BitDo Controller"]
    B["/joystick_node"]
    C["/joystick_data<br/>Joystick"]
    D["/joystick_bridge"]
    E["/local_driving<br/>[direction_rad, speed_cm_s, rotation_rad_s]"]
    F["/local_navigation_node"]
    G["/damiao_control<br/>[motor_id, 3, speed_rad_s, 0]"]
    H["/motor_controller_node"]
    I["Motor 1-4"]

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

解释：

```text
/joystick_node:
  读取手柄，发布 /joystick_data

/joystick_bridge:
  把左摇杆/右摇杆转换成底盘移动指令 /local_driving

/local_navigation_node:
  把底盘目标速度转换成 Motor 1-4 的轮速

/motor_controller_node:
  通过 USB-CAN 发送达妙电机命令
```

底盘相关 topic：

| Topic | Type | 数据格式 | 作用 |
|---|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | `lx ly rx ry l2 r2 buttons` | 手柄状态 |
| `/local_driving` | `std_msgs/msg/Float32MultiArray` | `[direction_rad, speed_cm_s, rotation_rad_s]` | 底盘目标运动 |
| `/damiao_control` | `std_msgs/msg/Float32MultiArray` | `[motor_id, mode, speed_rad_s, duration]` | 达妙电机命令 |

## 3. 机械臂 Motor 5/6/7 链路

```mermaid
flowchart TD
    Joy["/joystick_data"]

    EBridge["/elevator_joystick_bridge_node<br/>R1/L1"]
    ECmd["/elevator_speed_cmd<br/>[speed_rad_s]"]
    ECtrl["/elevator_controller_node"]
    EStatus["/elevator_status"]
    M5["Motor 5 Elevator"]

    HBridge["/horizontal_joystick_bridge_node<br/>D-pad"]
    HCmd["/horizontal_speed_cmd<br/>[speed_rad_s]"]
    HCtrl["/horizontal_controller_node"]
    HStatus["/horizontal_status"]
    M6["Motor 6 Horizontal"]

    GBridge["/arm_gripper_joystick_bridge_node<br/>R2/L2"]
    GCmd["/arm_gripper_speed_cmd<br/>[speed_rad_s]"]
    GCtrl["/arm_gripper_controller_node"]
    GStatus["/arm_gripper_status"]
    M7["Motor 7 Arm Gripper"]

    Damiao["/damiao_control"]
    Driver["/motor_controller_node"]

    Joy --> EBridge --> ECmd --> ECtrl --> Damiao --> Driver --> M5
    ECtrl --> EStatus

    Joy --> HBridge --> HCmd --> HCtrl --> Damiao
    Driver --> M6
    HCtrl --> HStatus

    Joy --> GBridge --> GCmd --> GCtrl --> Damiao
    Driver --> M7
    GCtrl --> GStatus
```

解释：

```text
bridge node:
  只负责把手柄按钮变成 speed_cmd

controller node:
  负责限速、timeout、发布 /damiao_control

/motor_controller_node:
  统一控制 Motor 1-7
```

机械臂相关 topic：

| Topic | Type | 数据格式 | 作用 |
|---|---|---|---|
| `/elevator_speed_cmd` | `Float32MultiArray` | `[speed_rad_s]` | Motor 5 目标速度 |
| `/horizontal_speed_cmd` | `Float32MultiArray` | `[speed_rad_s]` | Motor 6 目标速度 |
| `/arm_gripper_speed_cmd` | `Float32MultiArray` | `[speed_rad_s]` | Motor 7 目标速度 |
| `/elevator_status` | `Float32MultiArray` | `[target_speed, commanded_speed, timeout_active, motor_id]` | Motor 5 状态 |
| `/horizontal_status` | `Float32MultiArray` | `[target_speed, commanded_speed, timeout_active, motor_id]` | Motor 6 状态 |
| `/arm_gripper_status` | `Float32MultiArray` | `[target_speed, commanded_speed, timeout_active, motor_id]` | Motor 7 状态 |

## 4. Pneumatic / Arduino Relay 链路

```mermaid
flowchart LR
    Joy["/joystick_data"]
    Bridge["/pneumatic_gripper_joystick_bridge_node<br/>B/A/X"]
    Cmd["/pneumatic_gripper_cmd<br/>[D9_gripper, D8_height]"]
    Driver["/pneumatic_relay_driver_node"]
    Serial["USB Serial<br/>9600 baud<br/>[D9,D8]\\n"]
    Arduino["Arduino Mega"]
    Relay["Relay outputs<br/>D9 + D8"]
    Status["/pneumatic_gripper_status"]

    Joy --> Bridge --> Cmd --> Driver --> Serial --> Arduino --> Relay
    Driver --> Status
```

解释：

```text
/pneumatic_gripper_joystick_bridge_node:
  把 B/A/X 变成 [D9,D8]

/pneumatic_relay_driver_node:
  把 ROS topic [D9,D8] 变成 serial 字符串 "[D9,D8]\n"

Arduino:
  读取 serial 字符串
  parse 两个数字
  digitalWrite 控制 D9 / D8 relay
```

Relay 逻辑：

```text
D9 gripper:
  0 = OPEN
  1 = CLOSE

D8 height:
  0 = LOW
  1 = HIGH
```

常见命令：

| ROS data | Serial to Arduino | 含义 |
|---|---|---|
| `[1,0]` | `[1,0]\n` | CLOSE + LOW |
| `[0,0]` | `[0,0]\n` | OPEN + LOW |
| `[1,1]` | `[1,1]\n` | CLOSE + HIGH |
| `[0,1]` | `[0,1]\n` | OPEN + HIGH |

## 5. Keyboard Teleop 旁路

```mermaid
flowchart TD
    Keyboard["Keyboard input"]
    Teleop["/keyboard_teleop_node"]

    Local["/local_driving"]
    Elev["/elevator_speed_cmd"]
    Horiz["/horizontal_speed_cmd"]
    Grip["/arm_gripper_speed_cmd"]
    Pneu["/pneumatic_gripper_cmd"]

    Keyboard --> Teleop
    Teleop --> Local
    Teleop --> Elev
    Teleop --> Horiz
    Teleop --> Grip
    Teleop --> Pneu
```

注意：

```text
keyboard_teleop 不应和 joystick bridge 同时运行。
否则会有两个输入源同时发布相同 command topic。
```

## 6. Safety / Timeout Graph

```mermaid
flowchart TD
    A["/joystick_bridge<br/>no /joystick_data > 0.3s"]
    B["publish /local_driving = [0,0,0]"]

    C["/local_navigation_node<br/>no /local_driving > 0.3s"]
    D["Motor 1-4 speed = 0"]

    E["/motor_controller_node<br/>continuous VEL no refresh > 0.5s"]
    F["timed-out motor speed = 0"]

    G["r1_arm_control controllers<br/>speed_cmd timeout > 0.3s"]
    H["Motor 5/6/7 speed = 0"]

    I["/pneumatic_relay_driver_node<br/>no /pneumatic_gripper_cmd > 0.5s"]
    J["send [1,0] to Arduino<br/>CLOSE + LOW"]

    A --> B --> C --> D
    E --> F
    G --> H
    I --> J
```

## 7. Node Summary

| Node | Package | 主要作用 |
|---|---|---|
| `/joystick_node` | `my_joystick_driver` | 读取手柄，发布 `/joystick_data` |
| `/joystick_bridge` | `joystick_bridge` | 手柄摇杆到底盘 `/local_driving` |
| `/local_navigation_node` | `base_omniwheel_r2_700` | 底盘运动学，计算 Motor 1-4 轮速 |
| `/motor_controller_node` | `base_omniwheel_r2_700` | 达妙电机 driver，控制 Motor 1-7 |
| `/elevator_joystick_bridge_node` | `r1_arm_control` | R1/L1 fixed speed -> `/elevator_speed_cmd` |
| `/elevator_controller_node` | `r1_arm_control` | 控制 Motor 5 |
| `/horizontal_joystick_bridge_node` | `r1_arm_control` | D-pad -> `/horizontal_speed_cmd` |
| `/horizontal_controller_node` | `r1_arm_control` | 控制 Motor 6 |
| `/arm_gripper_joystick_bridge_node` | `r1_arm_control` | R2/L2 -> `/arm_gripper_speed_cmd` |
| `/arm_gripper_controller_node` | `r1_arm_control` | 控制 Motor 7 |
| `/pneumatic_gripper_joystick_bridge_node` | `arduino_pneumatic_driver` | B/A/X -> `/pneumatic_gripper_cmd` |
| `/pneumatic_relay_driver_node` | `arduino_pneumatic_driver` | ROS topic -> USB Serial -> Arduino |
| `/keyboard_teleop_node` | `keyboard_teleop` | 键盘调试输入，直接发布 command topics |

## 8. Node Pub/Sub Table

这个表直接说明每个 node 订阅什么、发布什么。

| Node | Subscribe | Publish | 说明 |
|---|---|---|---|
| `/joystick_node` | 无，读取 Linux evdev 硬件输入 | `/joystick_data` | 把手柄输入变成 ROS2 Joystick message |
| `/joystick_bridge` | `/joystick_data` | `/local_driving` | 把左/右摇杆变成底盘目标移动指令 |
| `/local_navigation_node` | `/local_driving` | `/damiao_control` | 把底盘目标移动换算成 Motor 1-4 轮速 |
| `/motor_controller_node` | `/damiao_control` | 无主要控制 topic；直接写 USB-CAN | 达妙电机 driver，控制 Motor 1-7 |
| `/elevator_joystick_bridge_node` | `/joystick_data` | `/elevator_speed_cmd` | R1/L1 转升降速度命令 |
| `/elevator_controller_node` | `/elevator_speed_cmd` | `/damiao_control`, `/elevator_status` | 控制 Motor 5 elevator |
| `/horizontal_joystick_bridge_node` | `/joystick_data` | `/horizontal_speed_cmd` | D-pad 转水平移动速度命令 |
| `/horizontal_controller_node` | `/horizontal_speed_cmd` | `/damiao_control`, `/horizontal_status` | 控制 Motor 6 horizontal |
| `/arm_gripper_joystick_bridge_node` | `/joystick_data` | `/arm_gripper_speed_cmd` | R2/L2 净输入经 `0.1x + 0.9x³` 转 Motor 7 速度命令 |
| `/arm_gripper_controller_node` | `/arm_gripper_speed_cmd` | `/damiao_control`, `/arm_gripper_status` | 控制 Motor 7 arm gripper motor |
| `/pneumatic_gripper_joystick_bridge_node` | `/joystick_data` | `/pneumatic_gripper_cmd` | B/A/X 转 Arduino relay command |
| `/pneumatic_relay_driver_node` | `/pneumatic_gripper_cmd` | `/pneumatic_gripper_status`，并写 USB Serial | 把 ROS command 变成 Arduino serial 字符串 |
| `/keyboard_teleop_node` | 键盘输入 | `/local_driving`, `/elevator_speed_cmd`, `/horizontal_speed_cmd`, `/arm_gripper_speed_cmd`, `/pneumatic_gripper_cmd` | 无手柄时的调试输入源 |

## 9. Topic Publisher / Subscriber Table

这个表从 topic 角度说明：谁发布、谁订阅、数据格式是什么。

| Topic | Type | Publisher | Subscriber | Data |
|---|---|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | `/joystick_node` | `/joystick_bridge`, `/elevator_joystick_bridge_node`, `/horizontal_joystick_bridge_node`, `/arm_gripper_joystick_bridge_node`, `/pneumatic_gripper_joystick_bridge_node` | 手柄轴和按键，轴范围 `-512..512` |
| `/local_driving` | `std_msgs/msg/Float32MultiArray` | `/joystick_bridge` 或 `/keyboard_teleop_node` | `/local_navigation_node` | `[direction_rad, speed_cm_s, rotation_rad_s]` |
| `/damiao_control` | `std_msgs/msg/Float32MultiArray` | `/local_navigation_node`, `/elevator_controller_node`, `/horizontal_controller_node`, `/arm_gripper_controller_node` | `/motor_controller_node` | `[motor_id, mode, speed_rad_s, duration]` |
| `/elevator_speed_cmd` | `std_msgs/msg/Float32MultiArray` | `/elevator_joystick_bridge_node` 或 `/keyboard_teleop_node` | `/elevator_controller_node` | `[speed_rad_s]` |
| `/horizontal_speed_cmd` | `std_msgs/msg/Float32MultiArray` | `/horizontal_joystick_bridge_node` 或 `/keyboard_teleop_node` | `/horizontal_controller_node` | `[speed_rad_s]` |
| `/arm_gripper_speed_cmd` | `std_msgs/msg/Float32MultiArray` | `/arm_gripper_joystick_bridge_node` 或 `/keyboard_teleop_node` | `/arm_gripper_controller_node` | `[speed_rad_s]` |
| `/pneumatic_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | `/pneumatic_gripper_joystick_bridge_node` 或 `/keyboard_teleop_node` | `/pneumatic_relay_driver_node` | `[D9_gripper_state, D8_height_state]` |
| `/elevator_status` | `std_msgs/msg/Float32MultiArray` | `/elevator_controller_node` | monitor / debug terminal | `[target_speed, commanded_speed, timeout_active, motor_id]` |
| `/horizontal_status` | `std_msgs/msg/Float32MultiArray` | `/horizontal_controller_node` | monitor / debug terminal | `[target_speed, commanded_speed, timeout_active, motor_id]` |
| `/arm_gripper_status` | `std_msgs/msg/Float32MultiArray` | `/arm_gripper_controller_node` | monitor / debug terminal | `[target_speed, commanded_speed, timeout_active, motor_id]` |
| `/pneumatic_gripper_status` | `std_msgs/msg/String` | `/pneumatic_relay_driver_node` | monitor / debug terminal | human-readable serial/status text |

## 10. Topic Meaning Details

### `/joystick_data`

```text
Publisher:
  /joystick_node

Subscribers:
  /joystick_bridge
  /elevator_joystick_bridge_node
  /horizontal_joystick_bridge_node
  /arm_gripper_joystick_bridge_node
  /pneumatic_gripper_joystick_bridge_node
```

这是所有 controller 输入的源头。底盘、机械臂、气动各自的 bridge node 都从这里读取手柄状态。

### `/local_driving`

```text
Publisher:
  /joystick_bridge
  或 /keyboard_teleop_node

Subscriber:
  /local_navigation_node
```

这是底盘高层移动指令，不是单个轮子的速度。`local_navigation_node` 会把它转换成 Motor 1-4 的 wheel speed。

### `/damiao_control`

```text
Publishers:
  /local_navigation_node
  /elevator_controller_node
  /horizontal_controller_node
  /arm_gripper_controller_node

Subscriber:
  /motor_controller_node
```

这是达妙电机统一底层控制 topic。Motor 1-7 最终都会走这里。

### `/pneumatic_gripper_cmd`

```text
Publisher:
  /pneumatic_gripper_joystick_bridge_node
  或 /keyboard_teleop_node

Subscriber:
  /pneumatic_relay_driver_node
```

这是 Arduino relay 控制 topic。它不会进入 `/damiao_control`，而是由 `pneumatic_relay_driver_node` 转成 USB Serial 字符串发给 Arduino。

## 11. 最重要的理解

```text
手柄输入只产生 /joystick_data。

底盘、机械臂、气动各自有 bridge node 把 /joystick_data 转成自己的 command topic。

达妙 Motor 1-7 最后都汇总到 /damiao_control，由 /motor_controller_node 统一发给电机。

Arduino pneumatic 不经过 /damiao_control。
它走 /pneumatic_gripper_cmd -> serial -> Arduino -> relay。
```

## Domain Isolation

The R1 node graph is only valid after ROS2 domain isolation is applied. The R1 startup script exports:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

If `/damiao_motor_controller`, `/global_navigation_node`, `/base/dummy_control`, or `/arm/damiao_control` appears on R1, those entries are from another ROS2 graph and must be isolated before testing.

## 2026-06-06 控制输入更新

`/joystick_bridge` 将左摇杆平移映射到 `0..150 cm/s`，右摇杆旋转映射到 `-1.2..1.2 rad/s`；两者均使用 `0.1x + 0.9x³`。START/SELECT 当前不参与底盘调速。

## 2026-06-07 Damiao 恢复状态 Topic

```mermaid
flowchart LR
    Feedback[Motor 1-7 CAN feedback] --> Driver[/motor_controller_node]
    Driver --> Status[/damiao_motor_status]
    Driver --> Gate{RECOVERING or WAIT_NEUTRAL?}
    Gate -->|Yes| Zero[only 0 rad/s]
    Gate -->|READY| Command[allow /damiao_control]
```

`/damiao_motor_status` 类型为 `std_msgs/msg/Float32MultiArray`，格式为 `[motor_id, state_code, feedback_fresh, is_enabled, feedback_age_sec, recovery_attempts, neutral_received]`。


## 2026-06-12 Motor 8 POS_VEL 实验链路

```text
/joystick_data
  -> /motor8_position_joystick_bridge_node
  -> /motor8_position_input [toggle_event, trim_input, input_valid]
  -> /motor8_position_controller_node
  -> /damiao_control [8, 2, speed_rad_s, target_position_rad]
  -> /motor_controller_node (damiao_node)
  -> USB-CAN
  -> Motor 8
```

状态链路：

```text
/damiao_motor_status -> /motor8_position_controller_node
/motor8_position_controller_node -> /motor8_position_status
```

Motor 7 原有 `/arm_gripper_speed_cmd` 链路保持不变。

## 2026-06-13 Motor 7/8 共享 selector

```text
/joystick_data
  -> /motor_position_selector_joystick_bridge_node
       START: selected_motor 7 <-> 8 (default 7)
       X: selected motor A/B
       L2/R2: selected motor trim
  -> /motor7_position_input -> /motor7_position_controller_node -> /damiao_control
  -> /motor8_position_input -> /motor8_position_controller_node -> /damiao_control
  -> /motor_controller_node -> Motor 7/8 POS_VEL
```

旧 Motor 7 `/arm_gripper_speed_cmd` 链路不再由主启动脚本运行。

## 2026-06-13 三位置状态

```text
X rising edge -> selected_position = (selected_position + 1) mod 3
0 -> 0 rad
1 -> +35 rad
2 -> -35 rad
```

该状态由 Motor 7/8 controller 独立保存，共享 selector 只负责把 X 事件路由给当前电机。


## 2026-06-15 人視角與 Motor6 現行節點圖

本節取代前文把 D-pad 直接連到 Motor6 的現行描述。

```mermaid
graph LR
    Joy[/joystick_data/]
    BaseBridge[joystick_bridge]
    View[/view_orientation<br/>Int32 0..3/]
    Driving[/local_driving/]
    Nav[local_navigation_node]
    Base[Motor 1-4]
    HorizontalBridge[horizontal_joystick_bridge_node<br/>L3/R3]
    HorizontalCmd[/horizontal_speed_cmd/]
    HorizontalCtrl[horizontal_controller_node]
    Motor6[Motor 6]

    Joy --> BaseBridge
    BaseBridge --> View
    BaseBridge --> Driving
    Driving --> Nav --> Base
    Joy --> HorizontalBridge --> HorizontalCmd --> HorizontalCtrl --> Motor6
```

```text
D-pad -> joystick_bridge view selection only
L3/R3 -> horizontal_joystick_bridge_node -> /horizontal_speed_cmd [-10/0/+10]
```

視角值為 `0=前、1=右、2=後、3=左`；左搖桿回中後才接受新值。本功能已於
2026-06-15 完成實機測試。

## 2026-06-18 Current Runtime Node Graph Override

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


## 2026-06-19 KFS gripper 人視角節點圖更新

本節取代 2026-06-15 中把 `/view_orientation` 解讀為 E-stop 方向的描述。節點連線不變，只有 `joystick_bridge` 的 D-pad 語義改為 KFS gripper 方向：

```text
D-pad -> joystick_bridge KFS-view selection only
/view_orientation -> KFS gripper view, 0=front, 1=right, 2=back, 3=left
joystick_bridge internal conversion -> E-stop/body-front view = (KFS view + 1) % 4
```

左搖桿回中後才接受新視角；右搖桿旋轉、Motor6 `L3/R3` 控制、`/local_driving` topic 與底層 `local_navigation_node` 均不變。


## 2026-06-19 KFS gripper 車頭標節點圖更新

本節取代同日 KFS `+1` 偏移方案。節點連線不變，D-pad 的語義為 KFS gripper／車頭方向：

```text
D-pad -> joystick_bridge KFS/body-front view selection only
/view_orientation -> KFS gripper/body-front view, 0=front, 1=right, 2=back, 3=left
joystick_bridge internal conversion -> body_front_view = KFS view
```

左搖桿回中後才接受新視角；右搖桿旋轉、Motor6 `L3/R3` 控制、`/local_driving` topic 與底層 `local_navigation_node` 均不變。


## 2026-06-19 KFS gripper 開機預設節點圖更新

節點連線不變。`joystick_bridge` 啟動預設改為：

```text
/view_orientation = 0
0 = KFS gripper / body-front in operator-frame front
```

D-pad 仍只更新視角，不直接命令底盤旋轉。


## 2026-06-19 KFS 車頭標 90 度校正節點圖更新

節點連線不變，`joystick_bridge` 的內部校正公式更新為：

```text
/view_orientation -> KFS gripper / visual-front view
joystick_bridge internal conversion -> body_front_view = (KFS view - 1) % 4
```

D-pad 仍只更新視角，不直接命令底盤旋轉。
