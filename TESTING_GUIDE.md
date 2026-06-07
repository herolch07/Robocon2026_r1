# R1 测试指南

本文件记录当前工作区内的测试方式。旧路径 `Robocon2026_r2/2026R2_ws` 和旧脚本 `start_full_control_chain.sh` 已不再作为当前 R1 流程使用。

## 1. 编译检查

```bash
cd /home/robotics/robocon/new_ws
colcon build --symlink-install
source install/setup.bash
```

## 2. 启动完整系统

```bash
./r1_start_base_1_0.sh
```

如果只做无硬件 topic 级检查，可以分别启动相关节点，而不启动硬件 driver。

## 3. 手柄链路测试

查看手柄输入：

```bash
ros2 topic echo /joystick_data
```

预期范围：

```text
lx/ly/rx/ry: -512 .. 512
dx/dy: -512, 0, 512
l2/r2: 0 .. 512
```

查看底盘桥接输出：

```bash
ros2 topic echo /local_driving
```

格式：

```text
data[0] = direction_rad
data[1] = speed_cm_per_sec
data[2] = rotation_rad_per_sec
```

## 4. 底盘测试

先确认低速默认值：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge max_rotation
```

当前默认应为：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
max_rotation = 1.2
rotation_linear_weight = 0.1
```

手动发布小速度测试：

```bash
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [1.5708, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [-1.5708, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 0.3]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 0.0]}"
```

预期：

```text
0 rad: 前进
+pi/2: 右移
-pi/2: 左移
rotation: 原地旋转
```

如果旋转方向相反：

```bash
ros2 param set /local_navigation_node rotation_axis_sign -1.0
```

## 5. 机械臂执行机构测试

升降：

```bash
ros2 topic pub --once /elevator_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.5]}"
ros2 topic echo /elevator_status
```

水平：

```bash
ros2 topic pub --once /horizontal_speed_cmd std_msgs/msg/Float32MultiArray "{data: [1.0]}"
ros2 topic echo /horizontal_status
```

机械夹爪电机：

```bash
ros2 topic pub --once /arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.3]}"
ros2 topic echo /arm_gripper_status
```

这些命令只发布一次，controller 会在 `timeout_sec = 0.3s` 后自动归零。

## 6. Pneumatic Gripper 测试

确认 Arduino 串口：

```bash
ls -l /dev/serial/by-id/
```

当前默认：

```text
/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0
```

发布命令：

```bash
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0, 0]}"
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 0]}"
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 1]}"
ros2 topic echo /pneumatic_gripper_status
```

含义：

```text
D9: 0 OPEN, 1 CLOSE
D8: 0 LOW, 1 HIGH
safe_state = [1,0]
```

## 7. Watchdog 测试

可以通过停止上游节点验证下游会归零：

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
```

预期：

```text
joystick_bridge: 0.3s 后发布 /local_driving = [0,0,0]
local_navigation_node: 0.3s 后 Motor 1-4 归零
damiao_node: 0.5s 后对应连续 VEL 电机归零
```

## 8. 测试记录表

| 测试项目 | 预期结果 | 实际结果 | 通过/失败 | 备注 |
|---------|---------|---------|----------|------|
| 手柄连接 | `/joystick_data` 有 -512..512 数据 | | | |
| 底盘前后 | 左摇杆上/下正确 | | | |
| 底盘横移 | 左摇杆左/右正确 | | | |
| 底盘旋转 | 右摇杆左/右原地旋转 | | | |
| Motor 5 | L1/R1 固定速度升降有响应 | | | |
| Motor 6 | D-pad 左/右有响应 | | | |
| Motor 7 | L2/R2 模拟调速有响应 | | | |
| Pneumatic | A/B/X 状态正确 | | | |
| Timeout | 停止输入后自动归零 | | | |

## ROS2 domain isolation check

测试前确认 R1 已隔离：

```bash
echo $ROS_DOMAIN_ID
echo $ROS_LOCALHOST_ONLY
ros2 node list
ros2 topic list
```

R1 不应看到 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control`。如果看到，先不要测试底盘，按 `ROS_DOMAIN_ISOLATION.md` 处理。

## 2026-06-06 混合曲线测试补充

当前平移上限为 `150 cm/s`，旋转上限为 `1.2 rad/s`，两者曲线均为 `0.1x + 0.9x³`。Motor 7 最大 `1.3 rad/s`，R2/L2 也使用同一曲线。测试顺序应为离地检查，再在安全区域逐步测试 10%/25%/50%/75%/100% 输入。START/SELECT 不再改变底盘速度。

## 2026-06-07 急停自动恢复测试

仅在底盘架空时测试。启动后监控 `ros2 topic echo /damiao_motor_status`，按下急停超过 10 秒，再释放急停且保持手柄回中。预期状态 `RECOVERING(0) -> WAIT_NEUTRAL(1) -> READY(2)`，无需重启 bash。释放急停时故意保持摇杆非零，电机必须保持零速；松杆回中后才可解锁。
