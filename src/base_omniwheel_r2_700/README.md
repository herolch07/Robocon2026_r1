# base_omniwheel_r2_700

ROS 2 motor control package for R2 omniwheel base.

## Changelog

### 2026-06-07 - v11 急停断电自动恢复与回中解锁
- `damiao_node` 记录每台 Motor 1-7 的最后反馈时间和使能状态。
- 反馈超过 `feedback_timeout_sec = 0.5 s` 未更新，或反馈显示 `isEnable = false` 时，该电机进入 `RECOVERING`。
- `RECOVERING` 期间只发送 `0 rad/s`，每 `recovery_retry_sec = 2.0 s` 自动重发 `VEL mode + enable + zero`，不会转发手柄非零命令。
- 收到新鲜的已使能反馈后进入 `WAIT_NEUTRAL`；必须先收到一次零速命令，才进入 `READY` 并恢复运动。
- USB-CAN 串口真的消失时改为低频无限重连；无需因为旧版 5 次上限重启 bash。
- 新增 `/damiao_motor_status`，用于查看每台电机恢复状态、反馈新鲜度和重试次数。

### 2026-05-16 - v4 横向平移修正与参数化
- **Local Navigation Node**: 将理想 45° 公式改为实机校准运动基底
  - 保持前进/后退的 `forward` 轮速组合不变
  - 将横向 `lateral` 与旋转 `rotation` 分离为独立 per-motor 系数
  - 解决左摇杆左/右横推时底盘原地旋转，而不是直接横移的问题
- **参数化改进**:
  - 新增 `wheel_base_radius_m`
  - 新增 `omniwheel_radius_m`
  - 新增 `rotation_axis_sign`
  - 新增 `motor_direction_1` ~ `motor_direction_4`
  - 新增 `forward_coeff_1` ~ `forward_coeff_4`
  - 新增 `lateral_coeff_1` ~ `lateral_coeff_4`
  - 新增 `rotation_coeff_1` ~ `rotation_coeff_4`
  - 以后轮距、轮径、电机方向、运动基底差异可通过参数调整，不需要复制 package
- **安全行为不变**:
  - `/local_driving` 输入 watchdog 保持 `command_timeout_sec = 0.3 s`
  - 超时后仍向 Motor 1-4 发布 `0 rad/s`

### 2026-05-16 - v5 轮速限幅与加速度保护
- **Local Navigation Node**: 新增输出保护，降低调试时 CAN/电机驱动断连风险
  - 新增 `max_wheel_speed_rad_s`，当前默认 `64.0 rad/s`
  - 新增 `max_wheel_accel_rad_s2`，默认 `12.0 rad/s²`
  - 斜向移动或平移+旋转叠加时，如果某个轮速超过限制，会按比例缩放全部轮速，保持运动方向但降低强度
  - 摇杆突然大幅移动时，会限制每个轮子的速度变化率，减少瞬时电流冲击
- **安全建议**:
  - 如果出现驱动器红灯、CAN 断连或必须重启电源，先降低 `max_wheel_speed_rad_s` 和 `max_wheel_accel_rad_s2`
  - 不建议在横向/斜向校准未完成前使用高速度测试

### 2026-01-29 (night - v3)
- **Local Navigation Node**: New high-level motion control node
  - Subscribes to `local_driving` topic for holonomic motion commands
  - Input format: `[direction_rad, plane_speed_cm/s, rotation_rad/s]`
  - Implements 4-wheel X-configuration inverse kinematics
  - Wheel base radius: 327.038 mm
  - Publishes individual motor commands to `damiao_control`
- **Omniwheel Kinematics**: X-type 4-wheel layout (45°, 135°, 225°, 315°)
  - Motor 1: Right Front (45°)
  - Motor 2: Left Front (135°)
  - Motor 3: Left Back (225°)
  - Motor 4: Right Back (315°)
- **Test Script**: `test_local_navigation.sh` for testing directional movements and rotation

### 2026-01-29 (evening - v2)
- **Auto-Stop Timer**: Implemented automatic motor stop after duration in VEL mode
  - When `mode == 3 (VEL)` and `param4 > 0`, motor stops automatically after specified time
  - Each motor has independent timer management
  - Previous timer cancelled if new command arrives for same motor
  - Example: `[1, 3, 5.0, 3.0]` → Motor 1 runs at 5 rad/s, auto-stops after 3 seconds
  - No need for manual mode 0 stop command when duration is set

### 2026-01-29 (evening - v1)
- **Auto-Reconnection**: Added automatic USB reconnection when motor power is lost
  - Reconnect interval: 2 seconds (configurable via `RECONNECT_INTERVAL`)
  - Max attempts: 5 (configurable via `RECONNECT_MAX_ATTEMPTS`, 0 = infinite)
  - Background health check every 2 seconds
  - Automatic hardware re-initialization on reconnection
- **Connection Status**: Added connection state monitoring and logging
- **Error Handling**: Enhanced serial communication error detection and recovery

### 2026-01-29 (afternoon)
- **Target Device**: Running on RDK X5 (Horizon Robotics Development Kit)
- **Environment Update**: Migrated from Docker to native Python venv (`venv_r2`)
- **Dependency Management**: Now using `uv` for package management (pyserial, numpy)
- **Launch File Update**: Removed `shooter` package references from launch configuration
- **Docker Deprecation**: Docker-related setup moved to `feat/docker` branch
- **Default Control Mode**: Changed default mode to VEL (speed control)
- **VEL Mode Support**: Added mode 3 (VEL) support in control callback
- **Message Format**: Updated to mode-dependent 4th parameter (position for POS_VEL, time for VEL)
- **Test Script**: New `test_damiao_vel.sh` for VEL mode testing (motors 1-4 at 5 rad/s for 5s)

### 2026-01-17 (afternoon)
- **DM_CAN Driver Fix**: Fixed critical `recv_buffer` initialization bug in MotorControl class
- **Motor Mode Switching**: Added support for all four control modes (MIT/POS_VEL/VEL/Disable)
- **Direct Motor Control**: New `direct_motor_test.py` with seamless mode switching capabilities
- **ROS2 Logging**: Migrated all print statements to professional ROS2 logging system
- **Multi-Motor Support**: Enhanced damiao_node.py to control all four motors simultaneously

### 2026-01-17（morning）
- Moved `run_r2_base_docker.sh` into this package
- Docker script now auto-sources ROS Jazzy and workspace setup on container start:
  - `source /opt/ros/jazzy/setup.bash`
  - `source /workspace/2026R2_ws/install/setup.bash`

## Nodes

### 1. damiao_node
Low-level motor driver for DM motors via USB-CAN interface.

### 2. local_navigation_node
High-level motion control for holonomic navigation.

### Legacy VESC nodes
Older notes mention `vesc_node` and `vesc_canbus_speed_control_node`. They are not part of the current R1 verified runtime in this workspace. The current verified motor path is `local_navigation_node -> damiao_node`.

## Topics

### Subscribed Topics
- **local_driving** (Float32MultiArray): High-level motion commands
  - Format: `[direction_rad, plane_speed_cm/s, rotation_rad/s]`
  - Subscribed by: `local_navigation_node`
  
- **damiao_control** (Float32MultiArray): Low-level motor commands
  - Format: `[motor_id, mode, speed, param4]`
  - Subscribed by: `damiao_node`

### Published Topics
- **/damiao_motor_status** (`std_msgs/msg/Float32MultiArray`): 每台电机恢复状态
  - Published by: `damiao_node`
  - Format: `[motor_id, state_code, feedback_fresh, is_enabled, feedback_age_sec, recovery_attempts, neutral_received]`
  - `state_code`: `0=RECOVERING`, `1=WAIT_NEUTRAL`, `2=READY`, `3=DISABLED`

## Node Architecture

```
[User/Strategy Layer]
        ↓
   local_driving topic [direction, speed, rotation]
        ↓
[local_navigation_node] ← inverse kinematics
        ↓
   damiao_control topic [motor_id, mode, speed, duration] × 4
        ↓
   [damiao_node] ← hardware driver
        ↓
   [USB-CAN Adapter]
        ↓
   [4× DM Motors]
```

## Parameters

### damiao_node Parameters
- **motor_ids**: 受控电机 ID，默认 `[1, 2, 3, 4, 5, 6, 7]`。
- **command_timeout_sec**: 连续 VEL 命令超时，默认 `0.5 s`；超时后对应电机发送 `0 rad/s`。
- **watchdog_hz**: 命令 watchdog 检查频率，默认 `20.0 Hz`。
- **feedback_timeout_sec**: 电机反馈失效阈值，默认 `0.5 s`；超时进入 `RECOVERING`。
- **recovery_retry_sec**: 恢复命令重试间隔，默认 `2.0 s`。
- **neutral_speed_threshold_rad_s**: 回中判定阈值，默认 `0.02 rad/s`。
- **status_hz**: `/damiao_motor_status` 发布频率，默认 `5.0 Hz`。
- **RECONNECT_INTERVAL**: USB-CAN 串口重连间隔，当前固定 `2.0 s`。
- **RECONNECT_MAX_ATTEMPTS**: 当前为 `0`，表示低频无限重连。

### local_navigation_node Parameters
- **wheel_base_radius_m**: Distance from wheel center to robot center (default: `0.327038 m`)
- **omniwheel_radius_m**: Omniwheel radius (default: `0.0635 m`)
- **lateral_axis_sign**: Lateral translation sign (default: `1.0`)
  - `1.0`: current verified default, joystick left produces left strafe on the tested R1/R2 base
  - Use `-1.0` if left/right translation direction is reversed on another hardware setup
- **rotation_axis_sign**: Rotation command sign (default: `1.0`)
  - Use `-1.0` if pure rotation direction is reversed on hardware
- **max_wheel_speed_rad_s**: Per-wheel speed limit before publishing to `/damiao_control` (default: `64.0 rad/s`)
  - If any wheel exceeds this value, all four wheel speeds are scaled together
- **max_wheel_accel_rad_s2**: Per-wheel acceleration limit (default: `12.0 rad/s²`)
  - Set to `0.0` to disable acceleration limiting
- **motor_direction_1** ~ **motor_direction_4**: Per-motor output sign (default: `[-1, 1, -1, 1]`)
  - Use `1.0` for normal direction, `-1.0` for reversed direction
- **forward_coeff_1** ~ **forward_coeff_4**: Forward/backward motion basis before motor direction (default: `[1, 1, -1, -1]`)
- **lateral_coeff_1** ~ **lateral_coeff_4**: Left/right motion basis before motor direction (default: `[1, -1, -1, 1]`)
- **rotation_coeff_1** ~ **rotation_coeff_4**: Rotation motion basis before motor direction (default: `[1, -1, 1, -1]`)
- **WHEEL_ANGLES**: X-configuration wheel angles
  - Motor 1 (Left Front): 45°
  - Motor 2 (Right Front): 135°
  - Motor 3 (Right Back): 225°
  - Motor 4 (Left Back): 315°
- **DEFAULT_MOTOR_MODE**: VEL mode (3) for continuous control
- **DEFAULT_DURATION**: 0.0 (continuous, updated by next command)

## Local Navigation Protocol

Topic: `local_driving` (Float32MultiArray)

**Message format**: `[direction_rad, plane_speed_cm/s, rotation_rad/s]`

### Parameter Definition

| Parameter | Unit | Range | Description |
|-----------|------|-------|-------------|
| `direction_rad` | radians | [-π, π] | Movement direction in robot coordinate system<br>• 0: Forward (robot's X+ axis)<br>• π/2: Right (robot's Y+ axis)<br>• π or -π: Backward<br>• -π/2: Left |
| `plane_speed_cm/s` | cm/s | [0, ∞) | Translational speed magnitude<br>• 0: No translation<br>• >0: Move at specified speed |
| `rotation_rad/s` | rad/s | (-∞, ∞) | Rotational speed<br>• 0: No rotation<br>• >0: Counter-clockwise rotation<br>• <0: Clockwise rotation |

### Coordinate System

```
Robot Top View (Front is Left Side):

    Y+ (Right)
      ↑
      |
      |
X- ← Robot → X+  (Back)    (Front)
      |
      |
      ↓
    Y- (Left)
```

**Note**: Due to robot's physical orientation, the "forward" direction in user commands is mapped to the robot's left side.

### Common Commands Examples

| Command | Direction | Speed | Rotation | Motion |
|---------|-----------|-------|----------|--------|
| `[0.0, 50.0, 0.0]` | 0° | 50 cm/s | 0 | Move forward |
| `[1.57, 30.0, 0.0]` | 90° | 30 cm/s | 0 | Move right |
| `[3.14, 40.0, 0.0]` | 180° | 40 cm/s | 0 | Move backward |
| `[-1.57, 25.0, 0.0]` | -90° | 25 cm/s | 0 | Move left |
| `[0.0, 0.0, 1.0]` | - | 0 | 1 rad/s | Rotate counter-clockwise |
| `[0.785, 35.0, 0.5]` | 45° | 35 cm/s | 0.5 rad/s | Move forward-right + rotate |
| `[0.0, 0.0, 0.0]` | - | 0 | 0 | Stop all motors |

### ROS2 Command Examples
```bash
# Move forward at 50 cm/s
ros2 topic pub /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 50.0, 0.0]}" --once

# Move right at 30 cm/s
ros2 topic pub /local_driving std_msgs/msg/Float32MultiArray "{data: [1.5708, 30.0, 0.0]}" --once

# Rotate CCW at 1 rad/s (no translation)
ros2 topic pub /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 1.0]}" --once

# Move forward-right at 40 cm/s while rotating CCW at 0.5 rad/s
ros2 topic pub /local_driving std_msgs/msg/Float32MultiArray "{data: [0.785, 40.0, 0.5]}" --once

# Stop (zero velocity)
ros2 topic pub /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 0.0]}" --once
```

## Motor Control Protocol (Low-Level)

Topic: `damiao_control` (Float32MultiArray)

**Message format**: `[motor_id, mode, speed, param4]`

The 4th parameter meaning depends on the control mode:

| motor_id | mode | speed | param4 | 说明 |
|----------|------|-------|--------|------|
| 1-4 | 0 | - | - | 停止/失能电机 |
| 1-4 | 3 (VEL) | rad/s | duration (s) | 速度控制模式，duration > 0 时自动停止 |
| 1-4 | 2 (POS_VEL) | rad/s | position (rad) | 位置速度控制 |

**VEL mode auto-stop behavior:**
- If `duration > 0`: Motor runs for specified time, then **auto-stops** (no manual stop needed)
- If `duration == 0`: Current version treats this as a continuous command that must be refreshed. If it is not refreshed, `damiao_node` watchdog sends `0 rad/s` after `command_timeout_sec` (default `0.5 s`).
- Timer is per-motor: sending new command to same motor cancels previous timer

**Examples:**
```bash
# VEL mode with auto-stop: Motor 1, 10 rad/s, auto-stops after 5 seconds
ros2 topic pub /damiao_control std_msgs/msg/Float32MultiArray "{data: [1.0, 3.0, 10.0, 5.0]}" --once

# VEL mode continuous refresh example: publish repeatedly in real control code.
# If this is published only once, the watchdog will stop Motor 1 after command_timeout_sec.
ros2 topic pub /damiao_control std_msgs/msg/Float32MultiArray "{data: [1.0, 3.0, 10.0, 0.0]}" --once

# POS_VEL mode: Motor 2, speed 1 rad/s, target position 50 rad
ros2 topic pub /damiao_control std_msgs/msg/Float32MultiArray "{data: [2.0, 2.0, 1.0, 50.0]}" --once

# Disable: Motor 3, stop immediately
ros2 topic pub /damiao_control std_msgs/msg/Float32MultiArray "{data: [3.0, 0.0, 0.0, 0.0]}" --once
```

## Auto-Reconnection（当前实现）

当前实现区分两种故障：

1. **USB-CAN 串口消失或关闭**：每 `2.0 s` 无限重连；重连后重新创建 Motor 1-7 并进入安全恢复状态。
2. **急停只切断电机电源，但 USB-CAN 仍由树莓派供电**：根据每台电机反馈超时/失能进入 `RECOVERING`，不依赖串口消失。

恢复流程：

```text
反馈超时或 isEnable=false
  -> RECOVERING，阻止所有非零命令
  -> 每 2.0s 向一台电机发送 VEL mode + enable + 0 rad/s
  -> 收到新鲜且 isEnable=true 的反馈
  -> WAIT_NEUTRAL，继续阻止非零命令
  -> 手柄/上游发送一次零速
  -> READY，允许正常控制
```

这样即使急停释放时操作者仍推着摇杆，电机也不会立即动作。旧版 changelog 中“最多 5 次重连”只描述 2026-01-29 版本，不是当前行为。

## Test Scripts

### High-Level Navigation Test
Script: `test_local_navigation.sh`
- Tests `local_navigation_node` with various motion commands
- Sequence: Forward → Right → Backward → Left → Rotation → Stop
- **Prerequisites**: Both `damiao_node` and `local_navigation_node` must be running

Run:
```bash
# Terminal 1: Start damiao_node
source /home/robotics/robocon2026_r1/r1_control_ws/install/setup.bash
ros2 run base_omniwheel_r2_700 damiao_node

# Terminal 2: Start local_navigation_node
source /home/robotics/robocon2026_r1/r1_control_ws/install/setup.bash
ros2 run base_omniwheel_r2_700 local_navigation_node

# Terminal 3: Run test
bash src/base_omniwheel_r2_700/test_local_navigation.sh
```

### Low-Level VEL Mode Test
Script: `test_damiao_vel.sh`
- Tests motors 1-4 in VEL mode
- Runs at 5 rad/s for 5 seconds
- Auto-detects ROS 2 version (Jazzy/Humble)

Run on host:
```bash
bash /home/robotics/robocon2026_r1/r1_control_ws/src/base_omniwheel_r2_700/test_damiao_vel.sh
```

### Single Motor Test
Script: `test_single_motor.sh`
- Tests motor 1 only
- Speed: 2 rad/s for 3 seconds
- Useful for quick testing

Run on host:
```bash
bash /home/robotics/robocon2026_r1/r1_control_ws/src/base_omniwheel_r2_700/test_single_motor.sh
```

### Diagnostic Tools
Scripts for debugging:
- `diagnose_damiao.sh` - System health check
- `debug_motor_communication.sh` - Communication debugging
- `start_damiao_node.sh` - One-click node startup

### POS_VEL Mode Test (Legacy)
- Auto-detects ROS 2 version by checking:
  - `/opt/ros/jazzy/setup.bash`
  - `/opt/ros/jazzy/setup.bash`
- Default test: mode 2 (pos_vel), position 50.0, speed 0.5

Run inside the container or on host:

```bash
bash test_damiao.sh
```

## Legacy Docker Notes

Docker was used in older R2 notes. The current R1 verified workflow runs directly from `/home/robotics/robocon2026_r1/r1_control_ws` and uses `./r1_start_base_1_0.sh`. The Docker paths below are historical references and may not exist in this workspace:

- `Robocon2026_r2/Dockerfile`
- `2026R2_ws/src/base_omniwheel_r2_700/run_r2_base_docker.sh`

Historical build/enter command:

```bash
sudo bash /home/robotics/robocon2026_r1/r1_control_ws/src/base_omniwheel_r2_700/run_r2_base_docker.sh
```

The script automatically sources ROS Jazzy and workspace setup, so you can run ROS commands immediately.

Inside the container:

```bash
bash /home/robotics/robocon2026_r1/r1_control_ws/src/base_omniwheel_r2_700/test_damiao.sh
```

Notes:
- The run script maps `/dev/serial/by-id/...` (or `/dev/ttyACM0`) into the container.
- If the device path changes, update the script or pass `--device` manually.

---

## 2026-05-14 安全更新：底盘与电机级 Watchdog

本节记录 2026-05-14 后新增的安全行为，用于覆盖上游 node 崩溃、topic 中断、手动发布连续速度命令后忘记停止等情况。

### local_navigation_node 输入超时保护

触发条件：

```text
超过 command_timeout_sec 没有收到 /local_driving
```

默认参数：

```text
command_timeout_sec = 0.3 s
watchdog_hz = 20.0 Hz
```

超时行为：

```text
向 Motor 1-4 发布 0 rad/s 速度命令
```

查看和调整：

```bash
ros2 param get /local_navigation_node command_timeout_sec
ros2 param set /local_navigation_node command_timeout_sec 0.3
```

### 横向平移校准说明

如果前进/后退正常，但左摇杆向左/向右时底盘原地旋转，说明横向基底打到了旋转组合。当前版本默认使用独立 `lateral_coeff_*` 修正。

先检查默认参数：

```bash
ros2 param get /local_navigation_node lateral_axis_sign
ros2 param get /local_navigation_node lateral_coeff_1
ros2 param get /local_navigation_node lateral_coeff_2
ros2 param get /local_navigation_node lateral_coeff_3
ros2 param get /local_navigation_node lateral_coeff_4
```

默认应该是：

```text
lateral_axis_sign = 1.0
lateral_coeff_1 = 1.0
lateral_coeff_2 = -1.0
lateral_coeff_3 = -1.0
lateral_coeff_4 = 1.0
```

如果在另一套硬件上左右方向刚好反了，可以改：

```bash
ros2 param set /local_navigation_node lateral_axis_sign -1.0
```

如果只有某一个轮子方向异常，再单独调整对应电机方向：

```bash
ros2 param set /local_navigation_node motor_direction_1 -1.0
ros2 param set /local_navigation_node motor_direction_2 1.0
ros2 param set /local_navigation_node motor_direction_3 -1.0
ros2 param set /local_navigation_node motor_direction_4 1.0
```

### 轮速限幅与加速度保护

触发条件：

```text
任意一个 wheel speed 超过 max_wheel_speed_rad_s
或某个 wheel speed 的变化率超过 max_wheel_accel_rad_s2
```

默认参数：

```text
max_wheel_speed_rad_s = 64.0 rad/s
max_wheel_accel_rad_s2 = 12.0 rad/s²
```

行为：

```text
wheel speed 超过上限时，四个轮子的速度一起按比例缩小
wheel speed 变化过快时，每个轮子按加速度上限渐变到目标值
```

低速排查建议：

```bash
ros2 param set /local_navigation_node max_wheel_speed_rad_s 1.5
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 6.0
```

恢复当前默认：

```bash
ros2 param set /local_navigation_node max_wheel_speed_rad_s 64.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 12.0
```

### damiao_node 电机级连续速度命令保护

触发条件：

```text
mode = 3 (VEL)
duration = 0.0
超过 command_timeout_sec 没有收到该 motor_id 的新速度命令
```

默认参数：

```text
command_timeout_sec = 0.5 s
watchdog_hz = 20.0 Hz
```

超时行为：

```text
只对超时的 motor_id 发送 0 rad/s
节点保持运行，不 disable 电机
```

注意：旧版文档中 `duration == 0` 被描述为“持续运行直到手动停止”。从 2026-05-14 安全更新后，这类连续速度命令必须被周期刷新；如果不刷新，将由 `damiao_node` watchdog 自动归零。

查看和调整：

```bash
ros2 param get /motor_controller_node command_timeout_sec
ros2 param set /motor_controller_node command_timeout_sec 0.5
```

## 2026-05-22 - v6 横向平移轮速基底修正

### 修改目标
- 修正 R1/R2 四轮 X 型全向底盘在左摇杆左右输入时只能四轮转动、车体不横移的问题。
- 当前实机轮位约定：Motor 1 = 左前，Motor 2 = 右前，Motor 3 = 右后，Motor 4 = 左后。

### local_navigation_node 接口
- 订阅：`/local_driving` (`std_msgs/Float32MultiArray`)
  - `[direction_rad, plane_speed_cm_s, rotation_rad_s]`
  - `direction_rad = 0` 表示前进，`+pi/2` 表示右移，`-pi/2` 表示左移。
- 发布：`/damiao_control` (`std_msgs/Float32MultiArray`)
  - `[motor_id, mode, speed_rad_s, duration]`
  - `mode = 3` 为达妙 VEL 模式，`duration = 0.0` 表示连续刷新。

### 当前运动基底默认值
- `forward_coeff_1..4 = [1, 1, -1, -1]`
- `lateral_coeff_1..4 = [1, -1, -1, 1]`
- `rotation_coeff_1..4 = [1, -1, 1, -1]`
- `motor_direction_1..4 = [-1, 1, -1, 1]`

说明：`lateral_coeff` 由旧版 `[-1, -1, -1, -1]` 改为 `[1, -1, -1, 1]`。旧组合会导致左右摇杆时轮子在转但横向力互相抵消；新组合使用 X 型全向轮的交叉横移基底。

### 超时保护
- `local_navigation_node` 保持 `command_timeout_sec = 0.3 s`。
- 如果超过该时间未收到 `/local_driving`，节点会向 Motor 1-4 发布 `0 rad/s`。
- `damiao_node` 仍有电机级 watchdog，连续 VEL 命令超时后对应电机归零。

### 最小测试命令
```bash
source /home/robotics/robocon2026_r1/r1_control_ws/install/setup.bash
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [1.5708, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [-1.5708, 10.0, 0.0]}"
```

如果横移方向反了，优先只改参数 `lateral_axis_sign`：

```bash
ros2 param set /local_navigation_node lateral_axis_sign 1.0
```

## 2026-05-22 - v7 左右方向与右摇杆原地旋转修正

### 修改目标
- 根据实机测试结果，左/右横移方向相反，因此将 `lateral_axis_sign` 默认值由 `-1.0` 改为 `1.0`。
- 修正右摇杆旋转基底，使 `rx` 输入用于底盘原地旋转，而不是混入平移。

### local_navigation_node 当前默认参数
- `lateral_axis_sign = 1.0`
- `rotation_axis_sign = 1.0`
- `lateral_coeff_1..4 = [1, -1, -1, 1]`
- `rotation_coeff_1..4 = [1, -1, 1, -1]`
- `motor_direction_1..4 = [-1, 1, -1, 1]`

叠加 `motor_direction_*` 后，右摇杆旋转输出为 checkerboard 轮速组合，目标行为是车体中心基本不平移，只绕自身中心转动。

### 测试建议
1. 左摇杆只测左/右横移，确认方向已正确。
2. 右摇杆只推左/右，确认底盘原地旋转。
3. 如果右摇杆旋转方向与操作习惯相反，只改参数：

```bash
ros2 param set /local_navigation_node rotation_axis_sign -1.0
```

### 安全保护
- `/local_driving` 超过 `command_timeout_sec = 0.3 s` 未刷新时，Motor 1-4 仍会收到 `0 rad/s`。
- `damiao_node` 的电机级 watchdog 仍作为第二层保护。

## 2026-05-22 - v8 实机最终确认版

### 实机确认结果
- 左摇杆前后、左右平移均可正常工作。
- 右摇杆左/右可控制底盘原地旋转。
- Motor 1-4 底盘、Motor 5 升降、Motor 6 水平移动、Motor 7 夹爪电机、Arduino pneumatic gripper 均已通过 controller 测试。

### 最终底盘默认参数
```text
Motor 1 = 左前
Motor 2 = 右前
Motor 3 = 右后
Motor 4 = 左后

lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4 = [1, 1, -1, -1]
lateral_coeff_1..4 = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

### Controller 最终映射
```text
左摇杆上/下: 底盘前进/后退
左摇杆左/右: 底盘左/右横移
右摇杆左/右: 底盘原地旋转
R2 / L2: Motor 5 升降正/反向
D-pad 左/右: Motor 6 水平移动
D-pad 上/下: Motor 6 水平移动速度档位增加/减少
R1 / L1: Motor 7 夹爪电机正/反向
B: pneumatic gripper OPEN，松开后 CLOSE
A: pneumatic height HIGH latch
X: pneumatic height LOW latch
```

### 启动方式
完整手柄控制系统使用根目录脚本：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./r1_start_base_1_0.sh
```

## 2026-05-22 - v9 右摇杆旋转基底复修

### 修改原因
- 实机复测发现 `[1, 1, 1, 1]` 会四轮转但车体不转，`[-1, 1, 1, -1]` 会变成反向横移；最终确认 `[1, -1, 1, -1]` 可实现右摇杆原地旋转。
- 前后移动和左右横移已经工作，因此本次只调整 rotation 基底，不修改 forward/lateral。

### 实机确认最终默认参数
```text
rotation_axis_sign = 1.0
rotation_coeff_1..4 = [1, -1, 1, -1]
```

### 测试方式
1. 重启 `local_navigation_node` 或重新运行 `./r1_start_base_1_0.sh`。
2. 只推右摇杆左/右，不碰左摇杆。
3. 期望结果：底盘绕自身中心原地旋转。
4. 如果旋转方向相反，只改：

```bash
ros2 param set /local_navigation_node rotation_axis_sign -1.0
```

## 2026-05-25 - v10 400 cm/s 轮速上限准备

### 修改目标
- 为底盘最高目标速度 `400 cm/s` 准备轮速上限。
- `local_navigation_node` 默认 `max_wheel_speed_rad_s` 从 `3.0` 改为 `64.0`。

### 计算依据
```text
wheel_radius_m = 0.0635
64.0 rad/s * 0.0635 m = 4.064 m/s = 406.4 cm/s
```

因此 `64.0 rad/s` 理论上可以覆盖 `joystick_bridge` 的 `400 cm/s` 最高速度档位。

### 安全说明
- `max_wheel_speed_rad_s` 只是轮速上限，不代表实机一定能稳定达到该速度。
- `max_wheel_accel_rad_s2` 当前仍为 `12.0 rad/s^2`，所以从低速加到高速会有加速度限制。
- 20kg 载重下应逐级升档，并观察电流、温度、打滑和驱动器状态。

## 2026-06-07 - v11 急停自动恢复测试

### 状态 Topic

```bash
ros2 topic echo /damiao_motor_status
```

每条消息对应一台电机：

```text
[motor_id, state_code, feedback_fresh, is_enabled, feedback_age_sec, recovery_attempts, neutral_received]
state_code: 0 RECOVERING, 1 WAIT_NEUTRAL, 2 READY, 3 DISABLED
feedback_age_sec = -1 表示启动后从未收到反馈
```

### 实机测试步骤

1. 将底盘架空，启动 `./r1_start_base_1_0.sh`，手柄保持回中。
2. 确认 Motor 1-7 最终为 `state_code = 2`。
3. 按下急停切断电机分电板，预期状态转为 `0`，且所有非零命令被阻止。
4. 释放急停，不重启 bash；节点每 `2.0 s` 自动重发模式、使能和零速。
5. 看到状态 `1` 后松开摇杆/按钮回中，状态应转为 `2`。
6. 小幅推动左摇杆确认底盘恢复。

### 参数调整

```bash
ros2 param get /motor_controller_node feedback_timeout_sec
ros2 param get /motor_controller_node recovery_retry_sec
ros2 param get /motor_controller_node neutral_speed_threshold_rad_s
ros2 param set /motor_controller_node recovery_retry_sec 3.0
```

不建议把 `feedback_timeout_sec` 调得过短，否则正常 CAN 抖动也可能触发恢复；不建议取消回中解锁。

### 2026-06-07 实机确认

- 急停按下超过 10 秒后，释放急停，无需重启 bash，Motor 1-7 可以自动恢复。
- 急停释放时保持摇杆非零，电机不会立即运动。
- 操作者松开摇杆回中后，状态由 `WAIT_NEUTRAL` 进入 `READY`，随后可重新正常控制。


## 2026-06-10 - v12 USB-CAN 串口权限诊断

### 问题判定

当日志包含以下内容时：

```text
Permission denied: /dev/ttyACM0
```

如果设备权限为 `root:dialout` 且当前用户不在 `dialout` 组，节点无法打开 USB-CAN 串口。节点现在会在 `Errno 13` 时打印对应的永久修复命令，同时保持断连安全状态并每 `2.0 s` 重试。

### 永久修复

```bash
sudo usermod -aG dialout robotics
```

执行后必须注销并重新登录，或重启系统。重新登录后确认：

```bash
id
ls -l /dev/ttyACM0
```

`id` 输出应包含 `dialout`。之后重新启动：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
./r1_start_base_1_0.sh
```

不建议长期使用 `sudo ros2 run` 或把设备设置为 `chmod 777`；前者会改变 ROS 环境和文件属主，后者会放宽所有本机用户的硬件访问权限。

## 2026-06-10 - v13 DM-S3519 反馈解析与轮速上限修正

### 当前硬件与单位

- 当前底盘电机型号按 **DM-S3519-1EC** 配置，不再使用旧代码中的 `DMH3510` 型号枚举。
- VEL 模式的 `V_desired` 和反馈 `dq` 均为减速器输出轴角速度，单位为 `rad/s`，不应再次除以约 `19.2:1` 的减速比。
- 规格书额定转速 `395 rpm` 约为 `41.36 rad/s`，空载最高转速 `435 rpm` 约为 `45.55 rad/s`。
- `local_navigation_node.max_wheel_speed_rad_s` 当前默认值改为 `40.0 rad/s`。本节取代旧版本中 `64.0 rad/s` 的当前配置说明；旧内容仅保留为历史记录。

轮半径为 `0.0635 m` 时，`40.0 rad/s` 对应轮缘线速度约 `2.54 m/s`。手柄 `150 cm/s` 纯平移指令约需 `23.62 rad/s`，因此该限幅不会直接把纯平移的 150 cm/s 截断；斜向、旋转叠加和标定矩阵可能使单轮需求更高，超过 `40.0 rad/s` 时四轮会按同比例缩放。

### CAN 反馈格式

USB-CAN 接收按完整 `16 byte` 帧解析：

```text
AA 11 XX CAN_ID[4] DATA[8] 55
```

DM-S3519 的 `DATA[0]` 低 4 bit 是电机 ID，高 4 bit 是使能/故障状态；`DATA[1:3]` 是位置，`DATA[3:5]` 是速度，`DATA[4:6]` 是转矩，`DATA[6]` 与 `DATA[7]` 分别是 MOS 和转子温度。旧实现把 `data[3]` 同时当成 ID、状态和速度的一部分，会造成电机编号错乱及 `q/dq` 长期饱和。

`/damiao_motor_status` 每台电机现追加以下字段：

```text
[7] error_code
[8] mos_temperature_c，未知时为 -1
[9] rotor_temperature_c，未知时为 -1
```

原有 `[0]..[6]` 字段保持不变。状态码 `1` 才视为已使能，其余状态进入现有恢复/零速保护流程。

### 参数边界与实机确认

驱动解码暂按 `PMAX=12.5 rad`、`VMAX=45 rad/s`、`TMAX=10 Nm` 映射。`PMAX/VMAX/TMAX` 是驱动器可写寄存器，必须读取实机寄存器确认；如果实机值不同，反馈物理量会按比例偏差，但原始 ID、状态和温度仍可正确解析。

实机验证命令：

```bash
ros2 param get /local_navigation_node max_wheel_speed_rad_s
ros2 topic echo /damiao_motor_status
```

架空底盘低速转动单个轮子时，应只更新对应 Motor，`error_code=1`，速度符号与指令一致，温度处于合理范围。反馈不新鲜、未使能或故障时，driver 会阻止非零命令并按既有 `feedback_timeout_sec`、`recovery_retry_sec` 参数执行安全恢复。
