# Robocon R1 ROS 2 工作区

[English](README.md) | 简体中文 | [繁體中文](README.zh-TW.md)

本仓库是 EdUHK Robotics Team @ Hero 开发的当前 R1 机器人控制工作区。

- GitHub：`herolch07`
- 当前最终操作指南：[r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md)
- 系统架构说明：[ARCHITECTURE.md](ARCHITECTURE.md)
- Node/topic 图：[NODE_GRAPH.md](NODE_GRAPH.md)
- 底盘速度调参说明：[SPEED_TUNING.md](SPEED_TUNING.md)
- 当前完整启动脚本：`./r1_start_base_1_0.sh`
- 项目记录中的当前实机确认日期：2026-05-22

## 当前系统

这个工作区是 Robocon R1 的 ROS 2 控制系统，包含：

- Motor 1-4：四轮全向底盘
- Motor 5：升降执行机构
- Motor 6：水平移动执行机构
- Motor 7：机械夹爪电机
- Arduino pneumatic gripper：气动夹爪开合与高度高/低
- 8BitDo 手柄输入，底层使用 Linux `evdev`
- 可选键盘遥控 package，用于低速调试

## 手柄映射

```text
左摇杆上/下：底盘前进/后退
左摇杆左/右：底盘左/右横移
右摇杆左/右：底盘原地旋转
R1 / L1：Motor 5 升降正/反向，固定速度
D-pad 左/右：Motor 6 水平移动
D-pad 上/下：Motor 6 水平移动速度档位 0.2 / 0.5 / 1.0
START / SELECT：当前不用于底盘调速
R2 / L2：Motor 7 机械夹爪正/反向，按压深度调速
B：按住 arm pneumatic gripper OPEN，松开 CLOSE
A：arm pneumatic height LOW 锁定
X：arm pneumatic height HIGH 锁定
Y：KFS staff gripper OPEN，松开 CLOSE
R3：当前不使用
```

## 当前重要默认值

```text
手柄摇杆范围：-512 .. 512
扳机范围：0 .. 512
手柄死区：15
joystick_bridge max_speed_cm：150.0
joystick_bridge max_rotation：1.2
joystick_bridge translation_linear_weight：0.1
joystick_bridge rotation_linear_weight：0.1
机械夹爪 max_speed_rad_s：1.3
机械夹爪 gripper_linear_weight：0.1
local_navigation_node max_wheel_speed_rad_s：64.0
joystick_bridge input_timeout_sec：0.3
local_navigation_node command_timeout_sec：0.3
damiao_node command_timeout_sec：0.5
pneumatic safe_state：[0, 1] = LOW + CLOSE
```

底盘运动学默认值：

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

## 快速启动

在机器人主机上运行：

```bash
cd /home/robotics/robocon/new_ws
colcon build --symlink-install
source install/setup.bash
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

脚本会启动 tmux session：

```text
r1_control
```

常用 tmux 命令：

```text
重新进入：tmux attach -t r1_control
离开但保持运行：Ctrl+b，然后按 d
关闭全部：tmux kill-session -t r1_control
```

## Package 一览

```text
src/my_joystick_msgs          自定义 Joystick 消息
src/my_joystick_driver        evdev 手柄驱动，发布 /joystick_data
src/joystick_bridge           手柄到底盘 /local_driving 的桥接
src/base_omniwheel_r2_700     全向底盘运动学与达妙电机驱动
src/r1_arm_control            Motor 5/6/7 速度控制与手柄桥接
src/kfs_staff_gripper       KFS/arm pneumatic 三路 Arduino relay aggregator
src/arduino_pneumatic_driver  Arduino relay 气动夹爪 joystick bridge
src/keyboard_teleop           键盘低速调试遥控
```

## 安全保护

当前控制链有多层 watchdog：

- `joystick_bridge`：`/joystick_data` 超时后发布 `/local_driving = [0, 0, 0]`。
- `local_navigation_node`：`/local_driving` 超时后让 Motor 1-4 归零。
- `damiao_node`：连续 VEL 命令超时后只让对应电机归零。
- `r1_arm_control` controllers：对应 speed command 超时后执行机构速度归零。
- `arduino_pneumatic_driver`：命令超时、重连、关闭时发送 `safe_state = [0, 1]`。

## 旧文档说明

本工作区里有一些历史报告。如果某段内容提到 `±8192`、`410` 手柄死区、`100 cm/s` 默认底盘速度、`start_all_nodes.sh`、`start_full_control_chain.sh`、VESC 节点，或旧路径 `Robocon2026_r2/2026R2_ws`，除非该段明确标成当前状态，否则应视为旧版记录。

当前操作以本 README 和 [r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md) 为准。

## ROS2 网络隔离

R1 启动脚本默认使用独立 ROS2 环境：

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

这样可以避免 R1 发现 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control` 等 node/topic。修改前请先阅读 `ROS_DOMAIN_ISOLATION.md`。

## 达妙电机急停自动恢复

电机反馈超时或失能后，driver 每 2 秒自动发送 `VEL + enable + zero`，并阻止非零命令。收到已使能反馈且手柄回中一次后才恢复运动。监控 `/damiao_motor_status`：`0=RECOVERING`、`1=WAIT_NEUTRAL`、`2=READY`、`3=DISABLED`。
