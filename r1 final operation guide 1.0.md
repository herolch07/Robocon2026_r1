# R1 Final Operation Guide 1.0

本指南记录当前可用版本的 R1 底盘和机械臂启动流程。当前版本已确认：

- 手柄必须使用 X 模式。
- 手柄数据范围是 `-128 ~ 128`，比旧版 `8192` 更容易读。
- `joystick_bridge` 默认最大平移速度是 `40 cm/s`。
- 全向轮半径按 `63.5 mm` 换算电机速度。
- Motor 5 是机械臂升降电机。
- Motor 6 是机械臂水平移动电机。
- Motor 7 是机械臂夹爪电机，默认夹爪速度是 `1.0 rad/s`。
- Motor 3 之前的反向响应慢问题已确认是 ESC 损坏导致；更换/修复 ESC 后问题已解决。

## 0. 启动前检查

确认硬件：

```bash
lsusb
ls -l /dev/ttyACM0
```

手柄需要能在 evdev 里看到：

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
python3 - <<'PY'
from evdev import InputDevice, list_devices
for path in list_devices():
    d = InputDevice(path)
    print(path, d.name)
PY
```

正常应看到类似：

```text
8BitDo Ultimate Wireless / Pro 2 Wired Controller
```

如果只在 `lsusb` 里看到 `8BitDo IDLE`，说明手柄还没有作为 controller 连接。把手柄切到 X 模式后重新插入。

## 1. 推荐一键启动

使用新的 tmux 启动脚本：

```bash
cd /home/robotics/robocon/new_ws
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

脚本会启动 tmux session：

```text
r1_control
```

窗口：

```text
0 joystick   手柄驱动
1 base_bridge 手柄到底盘转换
2 motors     达妙电机驱动
3 nav        全向轮运动学
4 elevator   升降电机控制
5 elev_bridge 手柄到升降控制
6 horizontal 水平电机控制
7 horiz_bridge 手柄到水平控制
8 gripper    夹爪电机控制
9 grip_bridge 手柄到夹爪控制
10 monitor   监控命令窗口
```

tmux 常用操作：

```text
切换窗口: Ctrl+b，然后按窗口编号
离开但保持运行: Ctrl+b，然后按 d
重新进入: tmux attach -t r1_control
关闭全部: tmux kill-session -t r1_control
```

## 2. 手动启动

如果不用脚本，开 10 个 terminal。

Terminal 1:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run my_joystick_driver joystick_node
```

Terminal 2:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run joystick_bridge joystick_bridge
```

Terminal 3:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run base_omniwheel_r2_700 damiao_node
```

Terminal 4:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run base_omniwheel_r2_700 local_navigation_node
```

Terminal 5:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control elevator_controller_node
```

Terminal 6:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control elevator_joystick_bridge_node
```

Terminal 7:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control horizontal_controller_node
```

Terminal 8:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control horizontal_joystick_bridge_node
```

Terminal 9:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control arm_gripper_controller_node
```

Terminal 10:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run r1_arm_control arm_gripper_joystick_bridge_node
```

## 3. 验证节点

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 node list
```

应看到：

```text
/joystick_node
/joystick_bridge
/motor_controller_node
/local_navigation_node
/elevator_controller_node
/elevator_joystick_bridge_node
/horizontal_controller_node
/horizontal_joystick_bridge_node
/arm_gripper_controller_node
/arm_gripper_joystick_bridge_node
```

## 4. 验证话题

手柄原始数据：

```bash
ros2 topic echo /joystick_data
```

现在手柄范围应是：

```text
lx/ly/rx/ry: -128 ~ 128
l2/r2: 0 ~ 128
```

底盘运动指令：

```bash
ros2 topic echo /local_driving
```

格式：

```text
data[0] = direction_rad
data[1] = speed_cm_per_sec
data[2] = rotation_rad_per_sec
```

电机命令：

```bash
ros2 topic echo /damiao_control
```

格式：

```text
data[0] = motor_id
data[1] = mode, 3 means VEL
data[2] = motor speed rad/s
data[3] = duration, 0 means continuous
```

机械臂升降速度：

```bash
ros2 topic echo /elevator_speed_cmd
```

机械臂水平速度：

```bash
ros2 topic echo /horizontal_speed_cmd
```

机械臂夹爪速度：

```bash
ros2 topic echo /arm_gripper_speed_cmd
```

## 5. 调速度

默认：

```text
max_speed_cm = 40.0
max_rotation = 2.0
deadzone = 6
```

查看：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge deadzone
```

设置：

```bash
ros2 param set /joystick_bridge max_speed_cm 40.0
ros2 param set /joystick_bridge max_rotation 1.0
```

更快：

```bash
ros2 param set /joystick_bridge max_speed_cm 60.0
ros2 param set /joystick_bridge max_rotation 1.5
```

速度调高前仍建议先低速试车，确认底盘响应正常。

## 6. 控制方式

```text
左摇杆上/下: 前进/后退
左摇杆左/右: 左右平移
右摇杆左/右: 原地旋转
R2: 升降电机正向
L2: 升降电机反向
D-pad 左/右: 水平电机左/右移动
D-pad 上: 水平电机加速档，0.2 -> 0.5 -> 1.0
D-pad 下: 水平电机减速档，1.0 -> 0.5 -> 0.2
R1: 夹爪正向
L1: 夹爪反向
```

所有操作建议先小幅推动摇杆。

## 7. Motor 3 记录

Motor 3 之前出现过反向响应慢的问题：

```text
连续反向命令时可以反向
突然从正向切到反向时响应明显慢于其他轮
```

最终确认原因是 ESC 损坏，不是软件速度计算问题。当前软件版本不再做强制停车或平滑补偿，底盘控制保持直接响应。

如果需要单独测试电机：

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
python3 motor_reversal_test.py --motor 3 --speed 10 --hold 2.0 --repeat 3
```

对比其他电机：

```bash
python3 motor_reversal_test.py --motor 1 --speed 10 --hold 2.0 --repeat 3
python3 motor_reversal_test.py --motor 2 --speed 10 --hold 2.0 --repeat 3
python3 motor_reversal_test.py --motor 4 --speed 10 --hold 2.0 --repeat 3
```

## 8. 停止系统

如果使用 tmux 脚本：

```bash
tmux kill-session -t r1_control
```

如果手动启动，在每个 terminal 按：

```text
Ctrl+C
```

如 ROS2 graph 缓存异常：

```bash
ros2 daemon stop
ros2 daemon start
```

## 9. Timeout / Watchdog 安全保护

当前版本有多层安全保护：

```text
joystick_bridge:
  超过 0.3s 没收到 /joystick_data
  -> 发布 /local_driving = [0, 0, 0]

local_navigation_node:
  超过 0.3s 没收到 /local_driving
  -> Motor 1-4 发布 0 rad/s

damiao_node:
  对 duration=0 的 VEL 连续命令
  超过 0.5s 没收到同一个 motor_id 的新命令
  -> 该 motor_id 发布 0 rad/s

r1_arm_control controllers:
  elevator / horizontal / arm_gripper
  超过 0.3s 没收到对应 speed_cmd
  -> 对应电机发布 0 rad/s
```

查看参数：

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
ros2 param get /elevator_controller_node timeout_sec
ros2 param get /horizontal_controller_node timeout_sec
ros2 param get /arm_gripper_controller_node timeout_sec
```

正常情况下不建议关掉这些 timeout。调试时如果需要改，只建议小范围调整，例如：

```bash
ros2 param set /joystick_bridge input_timeout_sec 0.5
ros2 param set /local_navigation_node command_timeout_sec 0.5
ros2 param set /motor_controller_node command_timeout_sec 0.8
```

## 10. 上传 GitHub

```bash
cd /home/robotics/robocon/new_ws
git status --short
git add .
git commit -m "Add R1 final operation guide and startup script"
git push origin main
```
