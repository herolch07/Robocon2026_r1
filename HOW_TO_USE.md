# R1 使用说明

本说明面向日常操作。当前完整系统以 `r1_start_base_1_0.sh` 为入口；`start.sh`、`start_background.sh` 只保留为旧底盘 4 节点流程，不建议作为 R1 完整系统首选。

## 日常启动

```bash
ssh robotics@你的机器人IP
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
./r1_start_base_1_0.sh
```

脚本会进入 tmux。离开但保持运行：

```text
Ctrl+b，然后按 d
```

重新进入：

```bash
tmux attach -t r1_control
```

停止全部：

```bash
tmux kill-session -t r1_control
```

## 手柄要求

- 8BitDo 手柄使用 X 模式。
- 当前 `Joystick.msg` 数值范围为 `-512 .. 512`。
- L2/R2 trigger 范围为 `0 .. 512`。
- 当前死区为 `15`（约满量程 2.93%）。

检查手柄：

```bash
python3 - <<'PY'
from evdev import InputDevice, list_devices
for path in list_devices():
    d = InputDevice(path)
    print(path, d.name)
PY
```

## 控制方式

```text
左摇杆上/下: 底盘前进/后退
左摇杆左/右: 底盘左/右横移
右摇杆左/右: 底盘原地旋转
R1: Motor 5 elevator 正向，固定速度
L1: Motor 5 elevator 反向，固定速度
D-pad 左/右: Motor 6 horizontal 左/右移动
D-pad 上/下: Motor 6 horizontal power level 增加/减少
START/SELECT: 当前不用于底盘调速
R2: Motor 7 arm gripper 正向，按压深度调速
L2: Motor 7 arm gripper 反向，按压深度调速
B: arm pneumatic gripper OPEN while held，松开 CLOSE
A: arm pneumatic height LOW latch
X: arm pneumatic height HIGH latch
Y: KFS staff gripper OPEN，松开 CLOSE
R3: 当前不使用
```

## 底盘速度曲线

当前默认配置：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
translation curve = 0.1x + 0.9x^3
max_rotation = 1.2
rotation_linear_weight = 0.1
rotation curve = 0.1x + 0.9x^3
```

查看：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge translation_linear_weight
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge rotation_linear_weight
ros2 param get /arm_gripper_joystick_bridge_node gripper_linear_weight
```

START/SELECT 当前不用于底盘调速。左摇杆平移与右摇杆旋转都使用 `0.1x + 0.9x³`；满杆分别达到 `150 cm/s` 和 `1.2 rad/s`。Motor 7 的 R2/L2 也使用同一曲线，满按达到 `1.3 rad/s`。

## 安全保护

当前链路有多层 timeout：

```text
joystick_bridge:
  /joystick_data 超过 0.3s 未更新
  -> /local_driving = [0,0,0]

local_navigation_node:
  /local_driving 超过 0.3s 未更新
  -> Motor 1-4 发送 0 rad/s

damiao_node:
  连续 VEL 命令超过 0.5s 未刷新
  -> 对应 motor_id 发送 0 rad/s

r1_arm_control:
  执行机构 speed_cmd 超过 0.3s 未刷新
  -> 对应 Motor 5/6/7 发送 0 rad/s

arduino_pneumatic_driver:
  /pneumatic_gripper_cmd 超过 0.5s 未刷新
  -> safe_state = [0,1] = LOW + CLOSE
```

## 常用检查

```bash
ros2 node list
ros2 topic list
ros2 topic echo /joystick_data
ros2 topic echo /local_driving
ros2 topic echo /damiao_control
ros2 topic echo /elevator_status
ros2 topic echo /horizontal_status
ros2 topic echo /arm_gripper_status
ros2 topic echo /pneumatic_gripper_status
```

## 如果没有反应

按顺序检查：

1. `tmux attach -t r1_control` 查看对应窗口是否退出。
2. `ros2 node list` 确认节点存在。
3. `ros2 topic echo /joystick_data` 确认手柄数据变化。
4. `ros2 topic echo /local_driving` 确认底盘指令变化。
5. 查看 `motors` 窗口确认达妙驱动已连接。
6. 确认 `/dev/ttyACM0` 是达妙 USB-CAN，Arduino relay 在 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`。

## ROS2 domain isolation

`r1_start_base_1_0.sh` now isolates R1 from R2 by exporting:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

Use SSH into R1 to run `ros2 node list` / `ros2 topic echo`. Do not remove this isolation unless remote ROS2 debugging from another computer is required.

## 2026-06-07 急停后自动恢复

`damiao_node` 现在会在反馈超时或电机反馈失能后自动执行 `VEL mode + enable + 0 rad/s`。恢复时不需要重启 bash，但必须先把摇杆和控制按钮全部松开回中，等 `/damiao_motor_status` 的 `state_code` 从 `0` 经过 `1` 变为 `2`，才允许再次运动。

```bash
ros2 topic echo /damiao_motor_status
```


## 2026-06-12 Motor 8 位置实验操作

```text
X: Motor 8 在位置 A/B 间切换
L3: Motor 8 负向微调
R3: Motor 8 正向微调
```

默认试验值为 A=`0.0 rad`、B=`0.3 rad`、软限位=`-0.5..0.5 rad`。第一次测试必须
离地或解除机构负载。启动后先确认：

```bash
ros2 topic echo /damiao_motor_status
ros2 topic echo /motor8_position_status
```

Motor 8 的 `/damiao_motor_status` 应显示 `motor_id=8`、`feedback_fresh=1`、
`enabled=1`、`active_control_mode=2`。没有看到这些状态时不要按 X。

## 2026-06-13 Motor 7/8 位置控制按键

```text
启动默认：Motor 7
START (+)：Motor 7 / Motor 8 切换
X：当前电机 A/B 切换
L2：当前电机负向微调
R2：当前电机正向微调
```

切换时必须先松开 X、L2、R2。查看当前选择：

```bash
ros2 topic echo /motor_position_selector_status
```

其中 `data[0]` 为当前电机 ID，正常启动应为 `7.0`。

## 2026-06-13 Motor 7/8 三位置操作

当前所选电机每短按一次 X：

```text
第一次：0 -> +35 rad
第二次：+35 -> -35 rad
第三次：-35 -> 0 rad
```

`/motor7_position_status` 或 `/motor8_position_status` 的 `data[3]` 表示当前预设：

```text
0 = 0 rad
1 = +35 rad
2 = -35 rad
```
