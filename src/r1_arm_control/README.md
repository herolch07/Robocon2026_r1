# r1_arm_control

R1 机械臂控制 package。当前用于控制速度型达妙电机执行机构：升降、水平移动、夹爪。

## 更新记录

### 2026-06-07 v4 Motor 7 混合三次曲线

- Motor 7 的 R2/L2 净输入改为 `y = 0.1x + 0.9x³`。
- 新增 `gripper_linear_weight = 0.1`，允许在 `0.0..1.0` 范围动态调整。
- `max_speed_rad_s = 1.3`、`trigger_deadzone = 24`、topic 和 controller watchdog 均保持不变。
- R2/L2 同时按下时先计算净输入；相同深度仍输出 `0 rad/s`。

### 2026-06-07 v3 升降与机械夹爪按键交换

- Motor 5 升降改为 `R1/L1` 数字按钮固定速度控制。
- `R1` 为升降正向，`L1` 为升降反向，同时按下或同时松开时停止。
- Motor 7 机械夹爪改为 `R2/L2` 模拟扳机控制。
- `R2` 为夹爪正向，`L2` 为夹爪反向，按压深度决定速度。
- Motor 7 旧的 0.5 s 两段速度与 START/SELECT 调速逻辑已移除。
- Motor ID、command topic 和 controller timeout 均不变。

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

### 2026-06-07 v2 Motor 7 两段式速度（历史记录，已被 v3 覆盖）

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
R1: 升降正向，固定速度
L1: 升降反向，固定速度
R1 + L1: 停止
发布: /elevator_speed_cmd
```

参数：

```text
command_speed_rad_s = 3.0
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
R2: 夹爪正向，按压越深速度越高
L2: 夹爪反向，按压越深速度越高
R2 + L2: 先计算两者净输入；相同深度时停止
曲线: y = 0.1x + 0.9x³
发布: /arm_gripper_speed_cmd
```

参数：

```text
max_speed_rad_s = 1.3
trigger_deadzone = 24
gripper_linear_weight = 0.1
trigger range = 0..512
```

理论目标速度（只按一个扳机）：

| 扳机深度 | Motor 7 速度绝对值 |
|---:|---:|
| 10% | 0.014 rad/s |
| 25% | 0.051 rad/s |
| 50% | 0.211 rad/s |
| 75% | 0.591 rad/s |
| 100% | 1.300 rad/s |

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
cd /home/robotics/robocon2026_r1/r1_control_ws
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


## 2026-06-12 v5 Motor 8 双位置 POS_VEL 实验

本版本不修改 Motor 7。新增 Motor 8 作为 DM-S3519 位置速度模式实验电机，复用唯一的
`damiao_node` 和现有 `/damiao_control` 底层接口。

### Nodes

#### motor8_position_joystick_bridge_node

订阅：

```text
/joystick_data my_joystick_msgs/msg/Joystick
```

发布：

```text
/motor8_position_input std_msgs/msg/Float32MultiArray
数据: [toggle_event, trim_input, input_valid]
```

默认控制：

```text
X: 在位置 A/B 之间切换，上升沿只触发一次
L3: 目标角度负向微调
R3: 目标角度正向微调
L3 + R3: 相互抵消
```

参数：

```text
toggle_button = "x"
negative_trim_button = "l3"
positive_trim_button = "r3"
publish_hz = 20.0 Hz
input_timeout_sec = 0.3 s
```

超过 `input_timeout_sec` 未收到 `/joystick_data` 后发布
`[0.0, 0.0, 0.0]`，禁止切换并停止微调。

#### motor8_position_controller_node

订阅：

```text
/motor8_position_input
/damiao_motor_status
```

发布：

```text
/damiao_control = [8.0, 2.0, max_speed_rad_s, target_position_rad]
/motor8_position_status = [target_q, actual_q, actual_dq, selected_position,
                           trim_input, feedback_valid, input_timeout,
                           motor_id, at_target]
```

默认参数仅用于低速离地实验：

```text
motor_id = 8
position_a_rad = 0.0 rad
position_b_rad = 0.3 rad
min_position_rad = -0.5 rad
max_position_rad = 0.5 rad
preset_speed_rad_s = 0.3 rad/s
trim_speed_rad_s = 0.1 rad/s
hold_speed_rad_s = 0.1 rad/s
position_tolerance_rad = 0.03 rad
input_timeout_sec = 0.3 s
feedback_timeout_sec = 0.5 s
publish_hz = 20.0 Hz
```

controller 只有在 Motor 8 反馈新鲜、已使能且驱动器报告 `POS_VEL` 时才发布运动命令。
启动、急停恢复或反馈重新出现时，先将目标同步为实时位置，不重放恢复前的旧预设。
手柄断连或 bridge topic 超时后，目标收回到实时位置并保持。所有预设和微调都经过
`min_position_rad` / `max_position_rad` 软限位。

### 启动

```bash
ros2 run r1_arm_control motor8_position_controller_node
ros2 run r1_arm_control motor8_position_joystick_bridge_node
```

完整系统执行 `./r1_start_base_1_0.sh` 时会自动启动这两个节点。

### 调试

```bash
ros2 topic echo /motor8_position_input
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
ros2 topic echo /damiao_control

ros2 param get /motor8_position_controller_node position_a_rad
ros2 param get /motor8_position_controller_node position_b_rad
ros2 param set /motor8_position_controller_node position_b_rad 0.2
```

首次实机测试必须让机构脱离负载或确保不会撞限位，并保持急停可立即操作。DM-S3519
上电位置会被当前 `damiao_node` 置为 `0 rad`，所以 A/B 是相对于本次启动位置的角度，
不是断电保持的机械绝对位置。

## 2026-06-13 v6 Motor 8 实机初测默认参数

Motor 8 在无危险机械负载的初步测试中，以下运行参数能够完成多圈位置控制，现固化为
`motor8_position_controller_node` 的源码默认值：

```text
position_a_rad = 0.0 rad
position_b_rad = 33.0 rad
min_position_rad = -35.0 rad
max_position_rad = 35.0 rad
preset_speed_rad_s = 3.0 rad/s
trim_speed_rad_s = 2.0 rad/s
```

换算后，位置 B 约为 `5.25` 圈，软限位单方向约为 `5.57` 圈。X 仍在 A/B 间切换，
L3/R3 仍在软限位内微调。该结果属于初测值，后续装入真实机构后仍需根据机械限位、
负载和方向继续调整。

注意：当前 DM-S3519 反馈解码参数仍使用 `PMAX = 12.5 rad`。虽然实机初测确认
`33 rad` 目标能够驱动电机多圈旋转，但超过 `+-12.5 rad` 后，必须继续观察
`actual_q` 是否饱和，以及到位判断、手柄断连保持和急停恢复后的当前位置同步是否可靠。
在这些保护行为完成实测前，不应直接把同样参数用于有碰撞风险的机构。
