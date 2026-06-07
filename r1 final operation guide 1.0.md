# R1 Final Operation Guide 1.0

本指南记录当前可用版本的 R1 底盘和机械臂启动流程。当前版本已确认：

- 手柄必须使用 X 模式。
- 手柄数据范围是 `-512 ~ 512`，比旧版 `8192` 更容易读。
- `joystick_bridge` 默认平移上限为 `150 cm/s`、旋转上限为 `1.2 rad/s`；左、右摇杆均使用 `0.1x + 0.9x³`，START/SELECT 不再调速。Motor 7 最大 `1.3 rad/s`，R2/L2 也使用同一曲线。
- 全向轮半径按 `63.5 mm` 换算电机速度。
- Motor 5 是机械臂升降电机。
- Motor 6 是机械臂水平移动电机。
- Motor 7 是机械臂夹爪电机，默认夹爪速度是 `1.0 rad/s`。
- Pneumatic gripper 通过 Arduino Mega USB Serial 控制，默认串口是 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`。
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
10 relay_panel KFS/arm pneumatic 共用 Arduino relay aggregator
11 pneu_bridge 手柄到 arm pneumatic gripper
12 kfs_bridge 手柄到 KFS staff gripper
13 monitor   监控命令窗口
```

tmux 常用操作：

```text
切换窗口: Ctrl+b，然后按窗口编号
离开但保持运行: Ctrl+b，然后按 d
重新进入: tmux attach -t r1_control
关闭全部: tmux kill-session -t r1_control
```

## 2. 手动启动

如果不用脚本，开 12 个 terminal。

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

Terminal 11:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run kfs_staff_gripper kfs_staff_gripper_arduino_node
```

Terminal 12:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run arduino_pneumatic_driver pneumatic_gripper_joystick_bridge_node
```

Terminal 13:

```bash
cd /home/robotics/robocon/new_ws
source install/setup.bash
ros2 run kfs_staff_gripper kfs_staff_gripper_joystick_bridge_node
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
/kfs_staff_gripper_arduino_node
/pneumatic_gripper_joystick_bridge_node
/kfs_staff_gripper_joystick_bridge_node
```

## 4. 验证话题

手柄原始数据：

```bash
ros2 topic echo /joystick_data
```

现在手柄范围应是：

```text
lx/ly/rx/ry: -512 ~ 512
l2/r2: 0 ~ 512
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

Pneumatic gripper 命令和状态：

```bash
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
ros2 topic echo /pneumatic_gripper_status
```

## 5. 平移速度曲线

默认：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
translation curve = 0.1x + 0.9x^3
max_rotation = 1.2
rotation_linear_weight = 0.1
rotation curve = 0.1x + 0.9x^3
arm gripper max_speed_rad_s = 1.3
gripper_linear_weight = 0.1
deadzone = 15
max_wheel_speed_rad_s = 64.0
```

查看：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge translation_linear_weight
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge rotation_linear_weight
ros2 param get /arm_gripper_joystick_bridge_node gripper_linear_weight
ros2 param get /joystick_bridge deadzone
```

START/SELECT 当前不用于调速。平移、旋转和 Motor 7 扳机输入均使用 `0.1x + 0.9x³`。第一次实机测试应先离地检查，再在安全区域小幅推杆或按压扳机。

## 6. 控制方式

```text
左摇杆上/下: 前进/后退
左摇杆左/右: 左右平移
右摇杆左/右: 原地旋转
R1: 升降电机正向，固定速度
L1: 升降电机反向，固定速度
D-pad 左/右: 水平电机左/右移动
D-pad 上: 水平电机加速档，0.2 -> 0.5 -> 1.0
D-pad 下: 水平电机减速档，1.0 -> 0.5 -> 0.2
START/SELECT: 当前不用于底盘调速
R2: 夹爪正向，按压深度调速
L2: 夹爪反向，按压深度调速
B: arm pneumatic gripper OPEN，松开后 CLOSE
A: arm pneumatic height LOW
X: arm pneumatic height HIGH
Y: KFS staff gripper OPEN，松开后 CLOSE
R3: 当前不使用
启动默认: height LOW + gripper CLOSE -> [0,1]
B 按住: gripper OPEN -> [current_height,0]
B 松开: gripper CLOSE -> [current_height,1]
A: height LOW -> [0,current_gripper]
X: height HIGH -> [1,current_gripper]
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

arduino_pneumatic_driver:
  启动默认 safe_state = [0,1]，即 LOW + CLOSE
  B 按下时发布 /pneumatic_gripper_cmd = [0,current_height]
  A 按下后 height 锁定为 HIGH
  X 按下后 height 锁定为 LOW
  超过 0.5s 没收到 /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
  -> driver 向 Arduino 发送 safe_state
```

查看参数：

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
ros2 param get /elevator_controller_node timeout_sec
ros2 param get /horizontal_controller_node timeout_sec
ros2 param get /arm_gripper_controller_node timeout_sec
ros2 param get /kfs_staff_gripper_arduino_node command_timeout_sec
ros2 param get /kfs_staff_gripper_arduino_node safe_state
ros2 param get /pneumatic_gripper_joystick_bridge_node open_state
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

## 10. 2026-05-22 最终实机确认记录

本节记录当前 GitHub 上传前的实机确认状态。

### 启动脚本

完整 controller 控制系统使用：

```bash
cd /home/robotics/robocon/new_ws
./r1_start_base_1_0.sh
```

该脚本会启动：

```text
Motor 1-4: omniwheel 底盘
Motor 5: elevator 升降
Motor 6: horizontal 水平移动
Motor 7: arm gripper motor
Arduino pneumatic: gripper open/close + height high/low
Joystick driver / bridge / monitor
```

### Controller 最终映射

```text
左摇杆上/下: 底盘前进/后退
左摇杆左/右: 底盘左/右横移
右摇杆左/右: 底盘原地旋转
R1: Motor 5 elevator 正向，固定速度
L1: Motor 5 elevator 反向，固定速度
D-pad 左/右: Motor 6 horizontal 左/右移动
D-pad 上: Motor 6 horizontal power level 增加，0.2 -> 0.5 -> 1.0
D-pad 下: Motor 6 horizontal power level 减少，1.0 -> 0.5 -> 0.2
START/SELECT: 当前不用于底盘调速
R2: Motor 7 arm gripper 正向，按压深度调速
L2: Motor 7 arm gripper 反向，按压深度调速
B: arm pneumatic gripper OPEN，松开后 CLOSE
A: arm pneumatic height LOW
X: arm pneumatic height HIGH
```

### 最终底盘运动学参数

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

### 实机结果

```text
底盘前后移动: OK
底盘左右横移: OK
底盘原地旋转: OK
Motor 5 elevator: OK
Motor 6 horizontal: OK
Motor 7 arm gripper: OK
Arduino pneumatic gripper: OK
```

### 2026-05-22 右摇杆旋转复修提醒

实机确认记录：`[1, 1, 1, 1]` 会让四个轮子转动但车体不旋转，`[-1, 1, 1, -1]` 会变成反向横移。最终确认右摇杆原地旋转使用：

```text
rotation_coeff_1..4 = [1, -1, 1, -1]
```

请重新运行 `./r1_start_base_1_0.sh` 后只测试右摇杆左/右。若方向相反，使用：

```bash
ros2 param set /local_navigation_node rotation_axis_sign -1.0
```

## ROS2 domain isolation note

R1 当前启动脚本固定使用：

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

这表示 R1 只看自己本机的 ROS2 node/topic，不会再看到 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control`。如果通过 SSH 登录 R1 查看 topic，此设置不影响使用。详细说明见 `ROS_DOMAIN_ISOLATION.md`。

## 2026-06-07 急停后自动恢复操作

急停会切断电机分电板，但树莓派供电的 USB-CAN 可能仍在线。当前 `damiao_node` 会根据电机反馈自动重新写入 VEL 模式并使能。释放急停后先松开全部摇杆、扳机和按钮，监控：

```bash
ros2 topic echo /damiao_motor_status
```

状态码 `0=RECOVERING`、`1=WAIT_NEUTRAL`、`2=READY`、`3=DISABLED`。Motor 1-7 全部到 `2` 后再小幅操作；正常情况不需要重启 `r1_start_base_1_0.sh`。
