# r1_arm_control

R1 机械臂控制 package。当前用于控制速度型达妙电机执行机构：升降、水平移动、夹爪。

## 更新记录

### 2026-05-14 v1 安全版本

- 新增并确认三个执行机构 controller：
  - `elevator_controller_node`
  - `horizontal_controller_node`
  - `arm_gripper_controller_node`
- 新增三个 joystick bridge：
  - `elevator_joystick_bridge_node`
  - `horizontal_joystick_bridge_node`
  - `arm_gripper_joystick_bridge_node`
- 所有 controller 均包含 `timeout_sec` 失效保护。
- 夹爪默认速度降为 `1.0 rad/s`，避免动作过快。

### 2026-06-07 v2 Motor 7 两段式速度

- `R1/L1` 按住前 `0.5 s` 使用 `0.3 rad/s`。
- 持续按住超过 `0.5 s` 后切换到高速档，默认 `1.3 rad/s`。
- `START (+)` / `SELECT (-)` 以 `0.1 rad/s` 调整高速档。
- 高速档限制在 `0.3 ~ 1.3 rad/s`。

## 适用范围

本 package 适用于 R1 当前机械臂的速度控制执行机构。node 绑定的是“升降 / 水平 / 夹爪”这类机构职责，不绑定某一年比赛流程或战术状态机。

## Nodes

### elevator_controller_node

订阅：

```text
/elevator_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control std_msgs/msg/Float32MultiArray
data = [motor_id, 3.0, speed_rad_s, 0.0]

/elevator_status std_msgs/msg/Float32MultiArray
data = [target_speed, commanded_speed, timeout_active, motor_id]
```

参数：

```text
motor_id = 5
max_speed_rad_s = 3.0
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

### horizontal_controller_node

订阅：

```text
/horizontal_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control
/horizontal_status
```

参数：

```text
motor_id = 6
max_speed_rad_s = 20.0
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

### arm_gripper_controller_node

订阅：

```text
/arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control
/arm_gripper_status
```

参数：

```text
motor_id = 7
max_speed_rad_s = 1.3
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

## Joystick Bridge Nodes

### elevator_joystick_bridge_node

```text
R2: 升降正向
L2: 升降反向
发布: /elevator_speed_cmd
```

### horizontal_joystick_bridge_node

```text
D-pad 左/右: 水平移动
D-pad 上: 提高速度档 0.2 -> 0.5 -> 1.0
D-pad 下: 降低速度档 1.0 -> 0.5 -> 0.2
发布: /horizontal_speed_cmd
```

### arm_gripper_joystick_bridge_node

```text
R1: 夹爪正向，前 0.5s 为 0.3 rad/s，之后进入高速档
L1: 夹爪反向，前 0.5s 为 0.3 rad/s，之后进入高速档
R1 + L1: 停止
START (+): 高速档增加 0.1 rad/s
SELECT (-): 高速档降低 0.1 rad/s
发布: /arm_gripper_speed_cmd
```

参数：

```text
slow_speed_rad_s = 0.3
fast_speed_rad_s = 1.3
hold_threshold_sec = 0.5
speed_adjust_step_rad_s = 0.1
min_fast_speed_rad_s = 0.3
max_fast_speed_rad_s = 1.3
```

## 超时保护

三个 controller 都实现相同的 timeout 逻辑。

触发条件：

```text
超过 timeout_sec 没有收到对应的 speed_cmd topic
```

默认值：

```text
timeout_sec = 0.3 s
```

超时行为：

```text
target_speed = 0.0
继续向 /damiao_control 发布 0 rad/s
status topic 中 timeout_active = 1.0
```

调整示例：

```bash
ros2 param set /elevator_controller_node timeout_sec 0.3
ros2 param set /horizontal_controller_node timeout_sec 0.3
ros2 param set /arm_gripper_controller_node timeout_sec 0.3
```

## 最小启动示例

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control arm_gripper_controller_node
```

另一个 terminal 发布测试命令：

```bash
source install/setup.bash
ros2 topic pub /arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.5]}" --once
```

如果只发布一次，`timeout_sec` 后会自动归零。

## 调试方式

```bash
ros2 topic echo /elevator_status
ros2 topic echo /horizontal_status
ros2 topic echo /arm_gripper_status
ros2 topic echo /damiao_control
```
