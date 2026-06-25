> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# R1 Final Operation Guide 1.0

本指南记录当前可用版本的 R1 底盘和机械臂启动流程。当前版本已确认：

- 手柄必须使用 X 模式。
- 手柄数据范围是 `-512 ~ 512`，比旧版 `8192` 更容易读。
- `joystick_bridge` 默认平移上限为 `150 cm/s`、旋转上限为 `3.0 rad/s`；左、右摇杆均使用 `0.1x + 0.9x³`，START/SELECT 不再调速。Motor 7 最大 `1.3 rad/s`，R2/L2 也使用同一曲线。
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
cd /home/robotics/robocon2026_r1/r1_control_ws
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
cd /home/robotics/robocon2026_r1/r1_control_ws
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

脚本会启动 tmux session：

```text
r1_control
```

窗口：

```text
0 joystick        手柄驱动 /joystick_node
1 op_mode         STAFF/KFS 模式选择 /operation_mode_selector_node
2 base_bridge     手柄到底盘与 D-pad 视角 /joystick_bridge
3 motors          达妙电机驱动 /motor_controller_node
4 nav             全向轮运动学 /local_navigation_node
5 elevator        Motor5 controller
6 elev_bridge     KFS mode L1/R1 -> elevator
7 horizontal      Motor6 controller
8 horiz_bridge    KFS mode L2/R2 -> horizontal
9 motor7_pos      Motor7 POS_VEL position controller
10 motor8_pos     Motor8 POS_VEL position controller
11 motor_select   STAFF mode A/X/R1/R2/L1/L2 -> Motor7/8 position input
12 relay_panel    五路 Arduino relay aggregator
13 pneu_bridge    STAFF B/Y/R3/L3 -> /pneumatic_gripper_cmd
14 kfs_bridge     KFS Y -> /kfs_staff_gripper_cmd
15 power_shutdown X+Y+B+A 长按 5 秒关机
16 monitor        监控命令窗口
```

tmux 常用操作：

```text
切换窗口: Ctrl+b，然后按窗口编号
离开但保持运行: Ctrl+b，然后按 d
重新进入: tmux attach -t r1_control
关闭全部: tmux kill-session -t r1_control
```

## 2. 手动启动

目前實機不建議手動開很多 terminal。正式入口只使用：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./r1_start_base_1_0.sh
```

如果必須手動排查，請直接參考 `r1_start_base_1_0.sh` 的 tmux window 命令順序；不要再啟動舊的 `arm_gripper_controller_node`、`arm_gripper_joystick_bridge_node` 或 `pneumatic_relay_driver_node`，避免 Motor7 的 VEL/POS_VEL 衝突或 Arduino serial port 被兩個 node 同時打開。

## 3. 验证节点

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
ros2 node list
```

應看到目前 start base 腳本啟動的節點：

```text
/joystick_node
/operation_mode_selector_node
/joystick_bridge
/motor_controller_node
/local_navigation_node
/elevator_controller_node
/elevator_joystick_bridge_node
/horizontal_controller_node
/horizontal_joystick_bridge_node
/motor7_position_controller_node
/motor8_position_controller_node
/motor_position_selector_joystick_bridge_node
/kfs_staff_gripper_arduino_node
/pneumatic_gripper_joystick_bridge_node
/kfs_staff_gripper_joystick_bridge_node
/joystick_shutdown_node
```

## 4. 验证话题

手柄原始数据：

```bash
ros2 topic echo /joystick_data
```

現在手柄範圍應是：

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
ros2 topic echo /damiao_motor_status
```

`/damiao_control` 格式：

```text
data[0] = motor_id
data[1] = mode, 2=POS_VEL, 3=VEL
data[2] = speed_rad_s / max_speed_rad_s
data[3] = duration_or_target_position
```

機構控制 topic：

```bash
ros2 topic echo /operation_mode
ros2 topic echo /view_orientation
ros2 topic echo /elevator_speed_cmd
ros2 topic echo /horizontal_speed_cmd
ros2 topic echo /motor7_position_input
ros2 topic echo /motor8_position_input
ros2 topic echo /motor7_position_status
ros2 topic echo /motor8_position_status
ros2 topic echo /motor_position_selector_status
```

Pneumatic / Arduino relay 命令和狀態：

```bash
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

## 5. 平移速度曲线

目前 source code 默认：

```text
joystick_bridge.max_speed_cm = 150.0
joystick_bridge.translation_linear_weight = 0.1
translation curve = 0.1x + 0.9x^3
joystick_bridge.max_rotation = 3.0 rad/s
joystick_bridge.rotation_linear_weight = 0.1
rotation curve = 0.1x + 0.9x^3
joystick_bridge.deadzone = 15
local_navigation_node.max_wheel_speed_rad_s = 40.0
local_navigation_node.max_wheel_accel_rad_s2 = 25.0
local_navigation_node.accel_limit_mode = per_wheel
```

查看：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge translation_linear_weight
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge rotation_linear_weight
ros2 param get /joystick_bridge deadzone
ros2 param get /local_navigation_node max_wheel_speed_rad_s
ros2 param get /local_navigation_node max_wheel_accel_rad_s2
ros2 param get /local_navigation_node accel_limit_mode
```

START/SELECT 不用於底盤調速；它們只切換 STAFF/KFS mechanism mode。第一次實機測試應先離地檢查，再在安全區域小幅推杆或按鍵。

## 6. 控制方式

```text
固定不變：
左搖桿上/下/左/右: 底盤按 D-pad 選定的人視角平移
右搖桿左/右: 底盤原地旋轉
D-pad: 設定 KFS gripper / visual front 在機手視角中的方向
X+Y+B+A 長按 5 秒: Raspberry Pi shutdown command

模式切換：
SELECT / 中左: STAFF mode (/operation_mode=1)
START / 中右: KFS mode (/operation_mode=2)

STAFF mode：
A: Motor7 90° / preset cycle
X: Motor8 90° / preset cycle
B: Motor7 staff gripper relay toggle
Y: Motor8 staff gripper relay toggle
R1/R2: Motor7 trim -/+
L1/L2: Motor8 trim -/+
R3/P1: Motor7 inclination/head relay toggle
L3/P2: Motor8 inclination/head relay toggle

STAFF mode 且 D-pad 下：
A -> Motor8 preset，X -> Motor7 preset
B -> Motor8 relay，Y -> Motor7 relay
R1 -> Motor8 trim positive，R2 -> Motor8 trim negative
L1 -> Motor7 trim positive，L2 -> Motor7 trim negative
R3/P1 -> Motor8 inclination，L3/P2 -> Motor7 inclination

KFS mode：
Y: KFS gripper toggle
L1/R1: Motor5 elevator negative/down、positive/up
L2/R2: Motor6 horizontal positive/out、negative/in
```

所有操作建议先小幅推动摇杆或短按按键確認方向。

## 7. Motor 3 记录

Motor 3 之前出现过反向响应慢的问题：

```text
连续反向命令时可以反向
突然从正向切到反向时响应明显慢于其他轮
```

最终确认原因是 ESC 损坏，不是软件速度计算问题。当前软件版本不再做强制停车或平滑补偿，底盘控制保持直接响应。

如果需要单独测试电机：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
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
  VEL motor 超过 0.5s 没收到新命令 -> 0 rad/s
  POS_VEL Motor7/8 超时 -> 使用最新反馈位置 hold position

r1_arm_control:
  elevator_controller / horizontal_controller 超过 0.3s 没收到 speed_cmd
  -> Motor5/Motor6 发布 0 rad/s
  motor7/8 position controller 输入无效或反馈超时
  -> 停止 trim / hold 安全位置

pneumatic_gripper_joystick_bridge_node:
  超过 0.3s 没收到 /joystick_data
  -> /pneumatic_gripper_cmd 回 STAFF safe_state [1,0,1,0]

kfs_staff_gripper_arduino_node:
  某一路來源超过 0.5s 没收到 command
  -> 只把該來源對應 relay group 回 full safe_state [0,1,0,1,0]
```

查看参数：

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
ros2 param get /elevator_controller_node timeout_sec
ros2 param get /horizontal_controller_node timeout_sec
ros2 param get /motor7_position_controller_node input_timeout_sec
ros2 param get /motor8_position_controller_node input_timeout_sec
ros2 param get /pneumatic_gripper_joystick_bridge_node input_timeout_sec
ros2 param get /pneumatic_gripper_joystick_bridge_node safe_state
ros2 param get /kfs_staff_gripper_arduino_node command_timeout_sec
ros2 param get /kfs_staff_gripper_arduino_node safe_state
```

正常情况下不建议关掉这些 timeout。调试时如果需要改，只建议小范围调整，例如：

## 10. 上传 GitHub

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
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
cd /home/robotics/robocon2026_r1/r1_control_ws
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

状态码 `0=RECOVERING`、`1=WAIT_NEUTRAL`、`2=READY`、`3=DISABLED`。Motor 1-8 全部到 `2` 后再小幅操作；正常情况不需要重启 `r1_start_base_1_0.sh`。


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
旋轉、`150 cm/s` 平移上限、`3.0 rad/s` 旋轉上限、`40 rad/s` 輪速上限及
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

## 2026-06-18 Historical Operation Override（已被五路 relay / STAFF-KFS mode 取代）

本節保留當時七路 relay 和 START/SELECT arm 選擇方案的歷史記錄，不再代表目前 source code 或實機操作。現在的正式狀態以 `CONTROLLER_USAGE.md`、`r1_start_base_1_0.sh`、`pneumatic_gripper_joystick_bridge_node.py`、`kfs_staff_gripper_arduino_node.py` 為準：Arduino 為五路 relay，`/pneumatic_gripper_cmd` 為四路 STAFF command，Motor7/8 由獨立 POS_VEL controller 控制。

保留仍然有效的部分：controller-gated autostart 可以由 `systemd/r1-control-autostart.service` 啟動 `scripts/wait_and_start_robot.sh`，等 8BitDo / Xbox controller active 後自動執行 `r1_start_base_1_0.sh`。預設 `STOP_ON_CONTROLLER_LOST=0`，手柄中途關掉不自動 kill 整套 ROS，仍依靠各 node watchdog 進安全輸出。

## 2026-06-19 Final STAFF Gripper / 90-Degree Split

This section supersedes any same-day text that says Y/A also toggle gripper relays.

Current STAFF mode split:

```text
Y  -> Motor7 left-right 90-degree / preset cycle only
A  -> Motor8 left-right 90-degree / preset cycle only
B  -> Motor7 staff gripper relay toggle only
X  -> Motor8 staff gripper relay toggle only
R1 -> Motor7 manual trim negative
R2 -> Motor7 manual trim positive
L1 -> Motor8 manual trim negative
L2 -> Motor8 manual trim positive
R3 -> Motor7 head / inclination relay toggle
L3 -> Motor8 head / inclination relay toggle
```

Current KFS mode remains:

```text
Y  -> KFS gripper toggle
L2 -> Motor6 horizontal positive / out
R2 -> Motor6 horizontal negative / in
L1 -> Motor5 elevator negative / down
R1 -> Motor5 elevator positive / up
```


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。

## 2026-06-20 KFS mechanism speed parameters

目前 source code 中 KFS mode 的機構速度如下：

```text
Motor5 elevator = 28.0 rad/s
  L1: negative/down
  R1: positive/up

Motor6 horizontal = 30.0 rad/s
  L2: positive/out at full trigger
  R2: negative/in at full trigger
```

對應參數：`elevator_joystick_bridge_node.command_speed_rad_s=28.0`、`elevator_controller_node.max_speed_rad_s=28.0`、`horizontal_joystick_bridge_node.command_speed_rad_s=30.0`、`horizontal_controller_node.max_speed_rad_s=30.0`。只有 `/operation_mode=2` 時生效；超時保護仍為 `timeout_sec=0.3 s`。

## 2026-06-20 STAFF D-pad Down Motor7/Motor8 Swap

目前 STAFF mode 會讀取 `/view_orientation`。規則：

```text
/view_orientation = 0  # D-pad 上，KFS visual front 在機手前方
  STAFF mapping 保持正常：Motor7 按鍵仍控制 Motor7，Motor8 按鍵仍控制 Motor8

/view_orientation = 2  # D-pad 下，KFS visual front 在機手後方
  STAFF mapping 對調：所有 Motor7 staff gripper 控制改送 Motor8，所有 Motor8 staff gripper 控制改送 Motor7
```

D-pad 左/右 (`1/3`) 目前不觸發對調，保持正常 mapping。對調只在 STAFF mode (`/operation_mode=1`) 影響 staff gripper 相關控制；KFS mode、底盤左/右搖桿、Motor5 elevator、Motor6 horizontal 不受影響。

正常 mapping：

```text
A -> Motor7 90° / preset
X -> Motor8 90° / preset
B -> Motor7 staff gripper relay
Y -> Motor8 staff gripper relay
R1/R2 -> Motor7 trim -/+
L1/L2 -> Motor8 trim -/+
R3/P1 -> Motor7 inclination/head relay
L3/P2 -> Motor8 inclination/head relay
```

D-pad 下 swap mapping：

```text
A -> Motor8 90° / preset
X -> Motor7 90° / preset
B -> Motor8 staff gripper relay
Y -> Motor7 staff gripper relay
R1/R2 -> Motor8 trim +/-   # R1/R2 also swapped, so R1 positive and R2 negative
L1/L2 -> Motor7 trim +/-   # L1/L2 also swapped, so L1 positive and L2 negative
R3/P1 -> Motor8 inclination/head relay
L3/P2 -> Motor7 inclination/head relay
```

相關參數：

```text
motor_position_selector_joystick_bridge_node.swap_staff_grippers_on_view_down = true
pneumatic_gripper_joystick_bridge_node.swap_staff_grippers_on_view_down = true
```

## 2026-06-20 Chassis Rotation Speed

Right stick rotation speed default is now:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

The rotation curve remains:

```text
rotation = (0.1x + 0.9x^3) * max_rotation
```

So small right-stick input still gives fine control, while full right-stick input can request up to `3.0 rad/s`. Actual chassis motion may still be scaled by `local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s` when translation and rotation are combined.

### 2026-06-20 STAFF D-pad Down Trim Direction Update

D-pad 下的 STAFF swap 現在也會把微調方向一起對調：`R1/R2` 互換、`L1/L2` 互換。因此 D-pad 下時：

```text
R1 -> Motor8 trim positive
R2 -> Motor8 trim negative
L1 -> Motor7 trim positive
L2 -> Motor7 trim negative
```

D-pad 上仍保持原本：`R1/R2=Motor7 -/+`，`L1/L2=Motor8 -/+`。

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
