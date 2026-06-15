# R1 测试指南

本文件记录当前工作区内的测试方式。旧路径 `Robocon2026_r2/2026R2_ws` 和旧脚本 `start_full_control_chain.sh` 已不再作为当前 R1 流程使用。

## 1. 编译检查

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
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


## 2026-06-12 Motor 8 POS_VEL 离地测试

1. 确认 Motor 8 的 CAN ID 已设为 `8`，机构不会撞限位，急停可立即操作。
2. 重新构建并启动：

```bash
colcon build --symlink-install --packages-select base_omniwheel_r2_700 r1_arm_control
source install/setup.bash
./r1_start_base_1_0.sh
```

3. 监控：

```bash
ros2 topic echo /motor8_position_input
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

4. 先短按 R3/L3，确认正负方向和微调保持；再按一次 X，目标应从 `0.0` 变为
`0.3 rad`；再次按 X 应回到 `0.0 rad`。
5. 拔掉手柄或停止 bridge 后，Motor 8 应停止继续追赶旧目标并保持实时位置。
6. 急停恢复后，必须先收到新鲜反馈并同步当前位置，旧的 A/B 目标不得自动重放。

根据实测临时调参：

```bash
ros2 param set /motor8_position_controller_node position_b_rad 0.2
ros2 param set /motor8_position_controller_node min_position_rad -0.3
ros2 param set /motor8_position_controller_node max_position_rad 0.3
ros2 param set /motor8_position_controller_node preset_speed_rad_s 0.2
```

## 2026-06-13 Motor 8 多圈参数复测

当前源码默认值：

```text
A = 0.0 rad
B = 33.0 rad
soft limit = -35.0..35.0 rad
preset speed = 3.0 rad/s
trim speed = 2.0 rad/s
```

复测时先保持无危险负载，并依次检查：X 到 B、X 回 A、L3/R3 两端软限位、松键保持、
手柄断连保持和急停恢复。同步监控：

```bash
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

特别记录 `actual_q` 在目标超过 `12.5 rad` 后是否继续真实增长。如果反馈固定在边界，
不能依赖当前反馈完成多圈到位、断连保持或恢复同步。

## 2026-06-13 Motor 7/8 共享按键测试

1. 启动后检查 `/motor_position_selector_status`，预期 `selected_motor_id = 7`。
2. 短按 Motor 7 的 L2/R2，确认只有 Motor 7 微调；X 控制 Motor 7 A/B。
3. 松开 X/L2/R2 后按 START，预期 selected ID 变为 8。
4. 再测试 L2/R2/X，确认只有 Motor 8 动作，Motor 7 保持。
5. 按住任一 L2/R2/X 时按 START，必须保持当前选择，`switch_blocked = 1`。
6. 手柄断连时，两台电机都停止修改目标并保持实时位置。

监控：

```bash
ros2 topic echo /motor_position_selector_status
ros2 topic echo /motor7_position_status
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

## 2026-06-13 Motor 7/8 三位置测试

对当前所选电机连续短按 X 三次，预期：

```text
按第1次：target_q = +35，selected_position = 1
按第2次：target_q = -35，selected_position = 2
按第3次：target_q = 0，selected_position = 0
```

切换到另一台电机后重复测试，确认两台电机的索引互不影响。测试多圈目标时保持急停可用，
并继续观察超过 `+-12.5 rad` 后的反馈是否真实可靠。


## 2026-06-13 六路 relay 与双 arm 无动力测试

先断开气源或移除危险负载，再启动系统：

```bash
ros2 topic echo /motor_position_selector_status
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

预期启动 command：

```text
/pneumatic_gripper_cmd = [0,1,0,1,1]
/kfs_staff_gripper_cmd = [0]
Arduino SENT = [0,0,1,0,1,1]
```

测试顺序：先确认默认 Motor7，按 A/B 只改变 command 第 1/2 项；松开全部按钮后按 START，
确认 selected ID=8，再按 A/B/SELECT，只应改变第 4/5/3 项。Y 始终只改变 KFS command。
停止 joystick 数据超过 0.3 s 后，arm command 应恢复 `[0,1,0,1,1]`；任一串口 command
来源停止超过 0.5 s 后，Arduino 聚合状态中该来源负责的 relay 应恢复安全值。


## 2026-06-14 手動人視角與 Motor6 測試

先架空底盤或在空曠區域低幅度測試。啟動後：

```bash
ros2 topic echo /view_orientation
ros2 topic echo /local_driving
ros2 topic echo /horizontal_speed_cmd
```

預期啟動 `/view_orientation=0`。依次測試：

1. E-stop 朝人前方，十字鍵上，左搖桿向前，`/local_driving data[0]` 約為 `0`。
2. 左搖桿回中，十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `+1.57 rad`。
3. 左搖桿回中，十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `-1.57 rad`。
4. 左搖桿回中，十字鍵下，狀態變為 `2`；左搖桿向前，方向約為 `+/-3.14 rad`。
5. 左搖桿未回中時按十字鍵，`/view_orientation` 不應改變；鬆開十字鍵及左搖桿後重按。
6. `L3` 預期 `/horizontal_speed_cmd=[-10.0]`。
7. `R3` 預期 `/horizontal_speed_cmd=[10.0]`。
8. 同時按 `L3+R3` 或全部鬆開，預期 `[0.0]`。

四方向確認完成後，再落地低速確認左搖桿方向與人的視角一致。沒有 IMU，車身旋轉或操作人
改變站位後必須手動重新設定十字鍵方向。

實機結果（2026-06-15）：以上人視角四方向與 Motor6 `L3/R3` 測試全部通過。
