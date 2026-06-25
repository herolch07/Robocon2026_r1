> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# keyboard_teleop

## 2026-06-20 Source-Verified Current Warning

`keyboard_teleop_node` 仍按舊調試接口發布 `/arm_gripper_speed_cmd` 和二值 `/pneumatic_gripper_cmd = [D9_gripper_state, D8_height_state]`。這符合目前 source code，但不符合正式五路 Arduino relay 比賽操作；正式操作請使用手柄和 `r1_start_base_1_0.sh`。

键盘临时遥控 package。它用于没有实体手柄时，在 Linux terminal 中用键盘发布机器人各子系统的既有控制 topic。

本 package 属于 operator input / teleop 层，不包含电机驱动、CAN/Serial 协议、底盘运动学、比赛流程或战术状态机。

---

## 更新记录 / Changelog

### 2026-05-16 v1 初始版本

- 新增 `keyboard_teleop_node`
- 支持键盘控制底盘、升降、水平移动、机械夹爪电机、气动夹爪
- 使用已有 ROS2 topic 接口拼装，不依赖其他 package 的内部实现
- 实现 `key_hold_sec` 输入失效保护：按键停止重复后自动输出零值
- 节点关闭或按 `SPACE` 时立即发布停止 / 安全命令

---

## 适用范围

适用于临时调试和低速测试：

- 全向底盘：通过 `/local_driving` 发布高层速度指令
- 速度型执行机构：通过单值 speed command topic 发布速度
- Arduino relay 气动夹爪：通过 `/pneumatic_gripper_cmd` 发布 `[D9,D8]`

不适用于正式比赛遥控，不负责轨迹规划，不负责底层硬件安全使能。

---

## Nodes

### keyboard_teleop_node

职责：

```text
interactive keyboard input
  -> existing subsystem command topics
```

订阅：

```text
无
```

发布：

```text
/local_driving std_msgs/msg/Float32MultiArray
data = [direction_rad, plane_speed_cm_s, rotation_rad_s]
频率 = publish_hz

/elevator_speed_cmd std_msgs/msg/Float32MultiArray
data = [speed_rad_s]
频率 = publish_hz

/horizontal_speed_cmd std_msgs/msg/Float32MultiArray
data = [speed_rad_s]
频率 = publish_hz

/arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray
data = [speed_rad_s]
频率 = publish_hz

/pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray
data = [D9_gripper_state, D8_height_state]
D9: 0 OPEN, 1 CLOSE
D8: 0 LOW, 1 HIGH
频率 = publish_hz
```

参数：

```text
publish_hz = 20.0
  发布频率，单位 Hz

key_hold_sec = 0.25
  按键保持时间，单位 s。超过此时间没有收到同一动作按键，就自动回零。

base_speed_cm = 25.0
  底盘键盘平移速度，单位 cm/s

base_rotation_rad_s = 1.0
  底盘键盘旋转速度，单位 rad/s

elevator_speed_rad_s = 1.0
  升降速度，单位 rad/s

horizontal_speed_rad_s = 4.0
  水平移动速度，单位 rad/s

arm_gripper_speed_rad_s = 0.5
  机械夹爪电机速度，单位 rad/s

initial_pneumatic_height = 0
  气动高度初始状态，0 LOW，1 HIGH
```

启动方式：

```bash
source install/setup.bash
ros2 run keyboard_teleop keyboard_teleop_node
```

可调速启动示例：

```bash
ros2 run keyboard_teleop keyboard_teleop_node --ros-args \
  -p base_speed_cm:=15.0 \
  -p base_rotation_rad_s:=0.5 \
  -p elevator_speed_rad_s:=0.5 \
  -p horizontal_speed_rad_s:=2.0 \
  -p arm_gripper_speed_rad_s:=0.25
```

---

## 键盘映射

```text
W/S: 底盘前进 / 后退
A/D: 底盘左移 / 右移
Q/E: 底盘逆时针 / 顺时针旋转

I/K: 升降正向 / 反向
J/L: 水平负向 / 正向
U/O: 机械夹爪电机负向 / 正向

B: 按住打开气动夹爪，松开关闭
H: 气动高度锁定 HIGH
N: 气动高度锁定 LOW

SPACE: 立即发布全部停止 / 安全命令
?: 重新打印按键说明
Ctrl+C: 退出节点
```

---

## 超时与失效保护

### 1. 键盘输入保持超时

触发条件：

```text
某个动作超过 key_hold_sec 没有收到新的按键重复输入
```

默认值：

```text
key_hold_sec = 0.25 s
```

超时行为：

```text
对应动作自动视为未按下
底盘 / 执行机构输出回到 0
B 不再保持时，气动 gripper 输出 CLOSE
```

修改方式：

```bash
ros2 run keyboard_teleop keyboard_teleop_node --ros-args -p key_hold_sec:=0.4
```

### 2. 手动停止

触发条件：

```text
按下 SPACE
```

行为：

```text
/local_driving 发布 [0.0, 0.0, 0.0]
/elevator_speed_cmd 发布 [0.0]
/horizontal_speed_cmd 发布 [0.0]
/arm_gripper_speed_cmd 发布 [0.0]
/pneumatic_gripper_cmd 发布 [1, current_height]
```

### 3. 节点关闭保护

触发条件：

```text
Ctrl+C 或 ROS shutdown
```

行为：

```text
退出前发布一次全部停止 / 安全命令
```

说明：

```text
下游 base_omniwheel_r2_700、r1_arm_control、arduino_pneumatic_driver
仍保留各自 watchdog。本节点的 key_hold_sec 是上游输入保护，
下游 timeout 是执行层保护。
```

---

## 接口约定

- `/local_driving` 的方向角沿用 `base_omniwheel_r2_700/local_navigation_node` 的约定
- 本节点只发布 topic，不读取其他 node 内部状态
- 不应与 `joystick_bridge`、`r1_arm_control/*_joystick_bridge_node`、`pneumatic_gripper_joystick_bridge_node` 同时运行，否则会有多个输入源同时发布相同 command topic

---

## 最小可运行示例

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --symlink-install --packages-select keyboard_teleop
source install/setup.bash
ros2 run keyboard_teleop keyboard_teleop_node
```

另一个 terminal 检查输出：

```bash
source install/setup.bash
ros2 topic echo /local_driving
```

---

## 调试方式与常见问题

### 没有反应

确认 terminal focus 在 `keyboard_teleop_node` 所在窗口。这个节点必须运行在 interactive Linux terminal 中。

### 一按就停

Linux terminal 的按键重复可能比较慢。可以适当增大：

```bash
ros2 run keyboard_teleop keyboard_teleop_node --ros-args -p key_hold_sec:=0.4
```

### 机器人收到互相冲突的命令

确认没有同时运行 joystick bridge：

```bash
ros2 node list
```

不应同时存在：

```text
/joystick_bridge
/elevator_joystick_bridge_node
/horizontal_joystick_bridge_node
/arm_gripper_joystick_bridge_node
/pneumatic_gripper_joystick_bridge_node
```

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
