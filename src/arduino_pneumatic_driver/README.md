# arduino_pneumatic_driver

Arduino Mega pneumatic relay gripper driver。此 package 通过 USB Serial 连接 Arduino Mega，并复用已测试的 Arduino 协议：

```text
[0,0]
[1,1]
[0,1]
[1,0]
```

Arduino 侧定义：

```text
Relay 1: arm gripper open/close
  0 = gripper OPEN
  1 = gripper CLOSE

Relay 2: arm gripper height
  0 = height LOW
  1 = height HIGH
```

## 更新记录

### 2026-05-15 v1 初始可运行版本

- 新增 `pneumatic_relay_driver_node`
- 新增 `pneumatic_gripper_joystick_bridge_node`
- 默认串口使用 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`
- 默认安全状态为 `[1,1]`，即 CLOSE
- 实现 command timeout，命令中断后自动发送 safe state

### 2026-05-15 v2 两路 pneumatic 分离

- D9 不再和 D8 一起被 A/B 同时改变。
- D9 定义为 gripper open/close。
- D8 定义为 gripper height high/low。
- joystick bridge 会记住两个 relay 的当前状态，按一个按钮只改变对应 relay。

### 2026-05-15 v3 持续发布当前状态

- `pneumatic_gripper_joystick_bridge_node` 改为 20Hz 持续发布当前 `[D9,D8]` 状态。
- 按键只更新内部状态，不再只发送一次命令。
- `/joystick_data` 超过 `input_timeout_sec` 未更新时，bridge 发布 `safe_state`。
- 这个版本用于避免 relay 在手柄命令和 driver timeout 之间来回闪烁。

### 2026-05-15 v4 只保留 gripper open 功能

- 回退 v3 的持续发布状态保持逻辑。
- 不再设计 height 控制按钮。
- D8 始终保持 HIGH。
- 只保留 `B -> [0,1]`，用于打开 gripper。
- 关闭与安全状态仍由 driver 的 `safe_state = [1,1]` 处理。

### 2026-05-15 v5 初始低位，A 后高度永久高位（历史记录，已被 v7 覆盖）

- 当时默认 driver safe state 改为 `[1,0]`，即 height LOW + gripper CLOSE；当前 v7 已改为 `[1,1]`。
- `B` 打开 gripper，保持当前 height。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A 之后 bridge 会持续刷新当前 `[D9,D8]`，防止 driver timeout 把 height 拉回 LOW。
- A 之后仍可用 `B` 打开 gripper，松开 B 后 gripper CLOSE，但 height 保持 HIGH。

### 2026-05-15 v6 增加 height LOW 锁定

- `X` 将 height 锁定为 LOW，即 D8=0。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A/X 都是锁定状态，直到另一个高度按钮被按下。
- `B` 仍然只控制 gripper OPEN，不改变 height。


### 2026-05-30 v7 适配新 relay 接线

- `A` 改为锁定 arm gripper OPEN。
- `X` 改为锁定 arm gripper CLOSE。
- `B` 改为按住 height LOW，松开 height HIGH。
- v7 曾让 bridge timeout 后发布 `[1,1]`；v8 已改为 `[1,0]`，启动和 timeout 默认 height LOW。
- KFS staff gripper 的 `Y` 映射不变。


### 2026-05-30 v8 启动默认 height LOW

- 启动 bash 后默认 arm height 为 LOW。
- `B` 按住时保持 height LOW。
- 只有在 `B` 被按过之后，松开 `B` 才会把 height 切到 HIGH。
- joystick timeout / driver timeout 后回 `[1,0]`，即 height LOW + gripper CLOSE。


### 2026-05-30 v9 实机确认 B 控 gripper，A/X 控 height

- 实机确认 `B` 控 arm gripper：按住 OPEN，松开 CLOSE。
- 实机确认 `A` 控 height LOW。
- 实机确认 `X` 控 height HIGH。
- 启动和 timeout 默认仍为 `[1,0]`：height LOW + gripper CLOSE。


### 2026-05-30 v10 实机确认 relay 顺序为 height/gripper

- 实机确认 relay command 顺序为 `[height_state, gripper_state]`。
- 启动和 timeout 默认改为 `[0,1]`：height LOW + gripper CLOSE。
- `B` 只改变第二位 gripper：按住 OPEN，松开 CLOSE。
- `A/X` 只改变第一位 height：A LOW，X HIGH。

## 适用范围

本 package 适用于 Arduino Mega + USB Serial + 2 路 relay / solenoid valve 的 pneumatic gripper。它不绑定某一年比赛流程，也不包含战术状态机。

## Nodes

### pneumatic_relay_driver_node

职责：

```text
ROS2 Int32MultiArray command
  -> USB Serial
  -> Arduino list command string
```

订阅：

```text
/pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray
data[0] = height state, 0 LOW, 1 HIGH
data[1] = gripper state, 0 OPEN, 1 CLOSE
```

发布：

```text
/pneumatic_gripper_status std_msgs/msg/String
```

参数：

```text
serial_port = /dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0
baud_rate = 9600
serial_timeout_sec = 0.1
command_timeout_sec = 0.5
watchdog_hz = 20.0
reconnect_sec = 1.0
safe_state = [0, 1]
```

### pneumatic_gripper_joystick_bridge_node

职责：

```text
/joystick_data
  -> button mapping
  -> /pneumatic_gripper_cmd
```

控制映射：

```text
B: hold arm gripper OPEN, release to CLOSE
A: latch arm height LOW
X: latch arm height HIGH
```

参数：

```text
initial_height_state = 0
publish_hz = 20.0
input_timeout_sec = 0.3
```

## 超时保护

`pneumatic_relay_driver_node` 实现 command timeout。

触发条件：

```text
超过 command_timeout_sec 没有收到 /pneumatic_gripper_cmd
```

默认值：

```text
command_timeout_sec = 0.5 s
```

超时行为：

```text
向 Arduino 发送 safe_state
默认启动 safe_state = [0,1] = LOW + CLOSE
```

当前 bridge 默认和 timeout 状态是 `[1,0]`，即 height LOW + gripper CLOSE。B 按住 OPEN、松开 CLOSE。A 锁定 height LOW，X 锁定 height HIGH。

`pneumatic_gripper_joystick_bridge_node` 也有 `/joystick_data` 输入 timeout。超过 `input_timeout_sec = 0.3 s` 后，bridge 会回到 `[1,0]`，即 height LOW + gripper CLOSE。

## 最小测试

启动 driver：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
ros2 run arduino_pneumatic_driver pneumatic_relay_driver_node
```

另一个 terminal：

```bash
source install/setup.bash
ros2 topic pub /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0, 0]}" --once
ros2 topic pub /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 1]}" --once
ros2 topic echo /pneumatic_gripper_status
```

## 调试

确认 Arduino 串口：

```bash
ls -l /dev/serial/by-id/
```

当前确认：

```text
/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0 -> /dev/ttyUSB0
```

注意不要使用 `/dev/ttyACM0`，它当前是达妙 USB-CAN。

## 2026-06-10 v11 arm height 单键切换

当前手柄映射更新为：

```text
B: 按住 arm gripper OPEN，松开 CLOSE
A: 每次按下在 height LOW/HIGH 之间切换
X: 不再用于 arm height，可供其他机构使用
```

切换只在按钮从松开变为按下的瞬间执行一次，长按 `A` 不会按 joystick 发布频率反复切换。bridge 仍以 `20 Hz` 发布 `[height_state, gripper_state]`，Arduino serial 协议和 relay 顺序不变：

```text
[0, 1] = height LOW + gripper CLOSE
[1, 1] = height HIGH + gripper CLOSE
```

新增参数：

```text
height_toggle_button = a
```

可在启动时改成其他 `Joystick` 消息按钮名。超过 `input_timeout_sec = 0.3 s` 未收到 `/joystick_data` 时，bridge 回到安全状态 `[0, 1]`，并要求按钮先松开，之后再次按下才允许切换。

## 2026-06-10 v12 arm gripper 单键锁定与默认 OPEN

本节取代旧版本中 `B` 按住控制和 arm gripper 默认 CLOSE 的当前行为说明；旧内容仅保留为历史记录。

当前手柄映射：

```text
A: 每次按下切换 arm height LOW/HIGH
B: 每次按下切换 arm gripper OPEN/CLOSE
X: 未分配给 arm pneumatic
```

启动默认状态和 `/joystick_data` 超时状态均为：

```text
[height_state, gripper_state] = [0, 0]
height LOW + arm gripper OPEN
```

A、B 都只在按钮上升沿切换，长按不会重复动作。启动或超过
`input_timeout_sec = 0.3 s` 未收到手柄数据后，A、B 必须先松开再重新按下，避免恢复通信时误切换。

正式启动脚本使用 `kfs_staff_gripper_arduino_node` 管理三路 Arduino relay；其完整默认串口状态为：

```text
[0, 0, 0] = arm LOW + arm OPEN + KFS CLOSE
```

standalone `pneumatic_relay_driver_node` 的默认 `safe_state` 同步改为 `[0, 0]`。注意：arm gripper 在手柄超时、节点重启、串口重连和正常关闭时都会回到 OPEN，可能释放正在夹持的物体，这是当前确认的预期行为。
