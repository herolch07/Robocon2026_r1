# R1 快速启动指南

本文件只记录当前 R1 完整控制系统的启动方式。旧的 4 节点底盘启动方式已经不是首选入口。

## 1. 启动前检查

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
```

确认设备：

```bash
lsusb
ls -l /dev/ttyACM0
ls -l /dev/serial/by-id/
```

确认手柄能被 evdev 看到：

```bash
python3 - <<'PY'
from evdev import InputDevice, list_devices
for path in list_devices():
    d = InputDevice(path)
    print(path, d.name)
PY
```

8BitDo 手柄需要使用 X 模式。当前手柄消息范围是：

```text
lx/ly/rx/ry: -512 .. 512
l2/r2: 0 .. 512
deadzone: 15
```

## 2. 编译

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --symlink-install
source install/setup.bash
```

## 3. 一键启动

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

脚本会启动 tmux session：

```text
r1_control
```

窗口内容：

```text
0 joystick
1 base_bridge
2 motors
3 nav
4 elevator
5 elev_bridge
6 horizontal
7 horiz_bridge
8 gripper
9 grip_bridge
10 relay_panel
11 pneu_bridge
12 kfs_bridge
13 monitor
```

## 4. 常用 tmux 操作

```text
重新进入: tmux attach -t r1_control
离开但保持运行: Ctrl+b，然后按 d
关闭全部: tmux kill-session -t r1_control
```

## 5. 控制映射

```text
左摇杆上/下: 底盘前进/后退
左摇杆左/右: 底盘左/右横移
右摇杆左/右: 底盘原地旋转
R1 / L1: Motor 5 升降正/反向，固定速度
D-pad 左/右: Motor 6 水平移动
D-pad 上/下: Motor 6 水平移动速度档 0.2 / 0.5 / 1.0
START/SELECT: 当前不用于底盘、Motor 5 或 Motor 7 调速
R2 / L2: Motor 7 机械夹爪正/反向，按压深度调速
B: arm pneumatic gripper OPEN while held，松开 CLOSE
A: arm pneumatic height LOW latch
X: arm pneumatic height HIGH latch
Y: KFS staff gripper OPEN，松开 CLOSE
R3: 当前不使用
```

## 6. 快速验证

```bash
ros2 node list
ros2 topic echo /joystick_data
ros2 topic echo /local_driving
ros2 topic echo /damiao_control
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

应至少看到：

```text
/joystick_node
/joystick_bridge
/motor_controller_node
/local_navigation_node
/elevator_controller_node
/horizontal_controller_node
/arm_gripper_controller_node
/kfs_staff_gripper_arduino_node
/pneumatic_gripper_joystick_bridge_node
/kfs_staff_gripper_joystick_bridge_node
```

## 7. 当前重要默认值

```text
joystick_bridge max_speed_cm = 150.0
joystick_bridge max_rotation = 1.2
joystick_bridge rotation_linear_weight = 0.1
arm gripper max_speed_rad_s = 1.3
arm gripper gripper_linear_weight = 0.1
joystick_bridge input_timeout_sec = 0.3
local_navigation_node command_timeout_sec = 0.3
local_navigation_node max_wheel_speed_rad_s = 64.0
damiao_node command_timeout_sec = 0.5
pneumatic safe_state = [0,1]
```

当前底盘平移不使用速度档。查看混合曲线参数：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge translation_linear_weight
ros2 param get /joystick_bridge rotation_linear_weight
ros2 param get /arm_gripper_joystick_bridge_node gripper_linear_weight
```

平移上限应为 `150.0`，旋转上限应为 `1.2`，三个曲线权重均应为 `0.1`。首次实机测试仍应小幅推动摇杆或扳机。

## ROS2 domain check

R1 startup script now sets:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

Before driving, confirm R1 cannot see R2-only topics such as `/base/dummy_control` or `/damiao_motor_controller`. Details: `ROS_DOMAIN_ISOLATION.md`.

## 2026-06-07 急停恢复快速检查

急停释放后保持手柄回中，不要重启脚本。运行 `ros2 topic echo /damiao_motor_status`；Motor 1-7 的 `state_code` 最终应为 `2`。`0` 表示正在恢复，`1` 表示等待回中，`2` 表示可控制。


## 2026-06-15 現行人視角底盤控制

此節為目前正式配置，取代文件前面所有「十字鍵控制 Motor6」或「L3／R3 未使用」的現行
描述；舊內容只保留作版本回溯。

```text
十字鍵上：E-stop／車頭在人視角前方，view=0
十字鍵右：E-stop／車頭在人視角右方，view=1
十字鍵下：E-stop／車頭在人視角後方，view=2
十字鍵左：E-stop／車頭在人視角左方，view=3
```

十字鍵只設定左搖桿的平移座標，不會命令底盤旋轉。左搖桿必須回中才接受視角切換；右搖桿
旋轉、`150 cm/s` 平移上限、`1.2 rad/s` 旋轉上限、`40 rad/s` 輪速上限及
`25 rad/s²` 四輪統一加速度限幅均保持不變。

Motor6 horizontal 已搬到：

```text
L3：-10 rad/s
R3：+10 rad/s
L3 + R3 或全部鬆開：0 rad/s
```

監控目前視角：

```bash
ros2 topic echo /view_orientation
```

本功能已於 2026-06-15 完成實機測試並確認繼續採用。
