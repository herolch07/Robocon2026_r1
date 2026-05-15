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
Relay 1 -> D9: gripper open/close
  0 = gripper OPEN
  1 = gripper CLOSE

Relay 2 -> D8: gripper height
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

### 2026-05-15 v5 初始低位，A 后高度永久高位

- 默认 driver safe state 改为 `[1,0]`，即 gripper CLOSE + height LOW。
- `B` 打开 gripper，保持当前 height。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A 之后 bridge 会持续刷新当前 `[D9,D8]`，防止 driver timeout 把 height 拉回 LOW。
- A 之后仍可用 `B` 打开 gripper，松开 B 后 gripper CLOSE，但 height 保持 HIGH。

### 2026-05-15 v6 增加 height LOW 锁定

- `X` 将 height 锁定为 LOW，即 D8=0。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A/X 都是锁定状态，直到另一个高度按钮被按下。
- `B` 仍然只控制 gripper OPEN，不改变 height。

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
data[0] = D9 gripper state, 0 OPEN, 1 CLOSE
data[1] = D8 height state, 0 LOW, 1 HIGH
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
safe_state = [1, 0]
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
B: gripper OPEN, keep current height
A: latch height HIGH
X: latch height LOW
```

参数：

```text
initial_height_state = 0
publish_hz = 20.0
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
默认启动 safe_state = [1,0] = CLOSE + LOW
```

默认启动后 safe state 是 `[1,0]`，即 gripper CLOSE + height LOW。按 A 后，bridge 会持续发布 height HIGH；按 X 后，bridge 会持续发布 height LOW。B 只临时打开 gripper，不改变 height。

## 最小测试

启动 driver：

```bash
cd /home/robotics/robocon/new_ws
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
