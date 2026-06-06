# R1 当前安全保护报告

本报告记录当前 R1 ROS 2 工作区的安全保护状态。旧版报告中关于 `±8192`、deadzone `410`、`joystick_bridge` 缺少 timeout、默认速度 `100 cm/s` 的内容已经过时。

## 当前输入范围

```text
Joystick lx/ly/rx/ry: -512 .. 512
Joystick dx/dy: -512, 0, 512
Joystick l2/r2: 0 .. 512
Joystick deadzone: 24
```

相关代码：

- `src/my_joystick_msgs/msg/Joystick.msg`
- `src/my_joystick_driver/my_joystick_driver/joystick_node.py`
- `src/joystick_bridge/joystick_bridge/joystick_bridge.py`

## 当前速度默认值

```text
joystick_bridge max_speed_cm = 20.0
joystick_bridge max_rotation = 0.5
local_navigation_node max_wheel_speed_rad_s = 64.0
local_navigation_node max_wheel_accel_rad_s2 = 12.0
```

这些默认值用于低速联调，降低横向、斜向、旋转叠加时的电流冲击。

## Watchdog 链路

### joystick_bridge

触发条件：

```text
超过 input_timeout_sec = 0.3 s 没有收到 /joystick_data
```

行为：

```text
发布 /local_driving = [0.0, 0.0, 0.0]
```

### local_navigation_node

触发条件：

```text
超过 command_timeout_sec = 0.3 s 没有收到 /local_driving
```

行为：

```text
向 Motor 1-4 发布 0 rad/s
```

### damiao_node

触发条件：

```text
mode = 3 (VEL)
duration = 0.0
超过 command_timeout_sec = 0.5 s 没有收到同一个 motor_id 的新速度命令
```

行为：

```text
只对超时 motor_id 发送 0 rad/s
节点保持运行，不 disable 电机
```

### r1_arm_control

触发条件：

```text
elevator / horizontal / arm_gripper speed command 超过 timeout_sec = 0.3 s 未刷新
```

行为：

```text
对应 Motor 5/6/7 继续发布 0 rad/s
status topic 中 timeout_active = 1.0
```

### arduino_pneumatic_driver

触发条件：

```text
超过 command_timeout_sec = 0.5 s 没有收到 /pneumatic_gripper_cmd
```

行为：

```text
发送 safe_state = [1,0] = CLOSE + LOW
```

同样在启动、重连、关闭时发送安全状态。

## 当前安全结论

- 手柄断线或 `joystick_node` 停止后，`joystick_bridge` 会主动让底盘上层命令归零。
- `local_navigation_node` 和 `damiao_node` 提供底盘双层兜底。
- Motor 5/6/7 controller 有独立 command timeout。
- Pneumatic driver 的默认安全状态是 `[1,0]`，即夹爪关闭、高度低位。
- 当前完整系统应使用 `./r1_start_base_1_0.sh` 启动。

## 建议

- 调试时先保留低速默认值：`max_speed_cm = 20.0`、`max_rotation = 0.5`。
- 只在实机方向确认后再逐步提高速度。
- 不建议关闭 timeout；如需调试，只做小范围增大。

## ROS2 domain isolation safety item

R1/R2 必须使用不同 ROS2 domain，避免同一网络内 DDS discovery 导致 node/topic 混线。R1 默认：

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

如果 R1 看到 `/damiao_motor_controller`、`/base/dummy_control` 或 `/global_navigation_node`，应视为 ROS graph 被其它机器人污染，禁止继续底盘测试。

## 2026-06-06 平移曲线更新

当前 `joystick_bridge` 默认上限为 `150 cm/s`，使用 `0.2x + 0.8x³` 混合三次曲线。输入 watchdog 和 `local_navigation_node` 轮速加速度限制不变。START/SELECT 不再切换速度档。
