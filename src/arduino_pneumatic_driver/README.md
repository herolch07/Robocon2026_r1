> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# arduino_pneumatic_driver


## 2026-06-20 Source-Verified Current State

目前正式啟動路徑只使用 `pneumatic_gripper_joystick_bridge_node`，不再啟動舊 `pneumatic_relay_driver_node`。本 package 現行輸出 topic 為四路 STAFF pneumatic command：

```text
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
DEFAULT_ARM_SAFE_STATE = [1,0,1,0]
```

STAFF mode source mapping：`B -> M7 gripper`，`Y -> M8 gripper`，`R3/P1 -> M7 inclination/head`，`L3/P2 -> M8 inclination/head`。當 `/view_orientation=2`（D-pad 下）時，Motor7/Motor8 relay controls 會對調。

完整 Arduino 五路 serial owner 在 `kfs_staff_gripper` package：

```text
/kfs_staff_gripper_arduino_node
full relay order = [KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
full safe_state = [0,1,0,1,0]
```

本 README 前面較舊的二路、六路、七路 relay 記錄只作歷史回溯，不代表目前 start base 實機 wiring。

## 更新记录

### 2026-05-15 v1 初始可运行版本

- 新增 `pneumatic_relay_driver_node`
- 新增 `pneumatic_gripper_joystick_bridge_node`
- 默认串口使用 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`
- 默认安全状态为 `[1,1]`，即 CLOSE
- 实现 command timeout，命令中断后自动发送 safe state

### 2026-05-15 v2 两路 pneumatic 分离

- D9 不再和 D8 一起被 A/B 同时改变。
- D9 定义为 gripper open/close。
- D8 定义为 gripper height high/low。
- joystick bridge 会记住两个 relay 的当前状态，按一个按钮只改变对应 relay。

### 2026-05-15 v3 持续发布当前状态

- `pneumatic_gripper_joystick_bridge_node` 改为 20Hz 持续发布当前 `[D9,D8]` 状态。
- 按键只更新内部状态，不再只发送一次命令。
- `/joystick_data` 超过 `input_timeout_sec` 未更新时，bridge 发布 `safe_state`。
- 这个版本用于避免 relay 在手柄命令和 driver timeout 之间来回闪烁。

### 2026-05-15 v4 只保留 gripper open 功能

- 回退 v3 的持续发布状态保持逻辑。
- 不再设计 height 控制按钮。
- D8 始终保持 HIGH。
- 只保留 `B -> [0,1]`，用于打开 gripper。
- 关闭与安全状态仍由 driver 的 `safe_state = [1,1]` 处理。

### 2026-05-15 v5 初始低位，A 后高度永久高位（历史记录，已被 v7 覆盖）

- 当时默认 driver safe state 改为 `[1,0]`，即 height LOW + gripper CLOSE；当前 v7 已改为 `[1,1]`。
- `B` 打开 gripper，保持当前 height。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A 之后 bridge 会持续刷新当前 `[D9,D8]`，防止 driver timeout 把 height 拉回 LOW。
- A 之后仍可用 `B` 打开 gripper，松开 B 后 gripper CLOSE，但 height 保持 HIGH。

### 2026-05-15 v6 增加 height LOW 锁定

- `X` 将 height 锁定为 LOW，即 D8=0。
- `A` 将 height 锁定为 HIGH，即 D8=1。
- A/X 都是锁定状态，直到另一个高度按钮被按下。
- `B` 仍然只控制 gripper OPEN，不改变 height。


### 2026-05-30 v7 适配新 relay 接线

- `A` 改为锁定 arm gripper OPEN。
- `X` 改为锁定 arm gripper CLOSE。
- `B` 改为按住 height LOW，松开 height HIGH。
- v7 曾让 bridge timeout 后发布 `[1,1]`；v8 已改为 `[1,0]`，启动和 timeout 默认 height LOW。
- KFS staff gripper 的 `Y` 映射不变。


### 2026-05-30 v8 启动默认 height LOW

- 启动 bash 后默认 arm height 为 LOW。
- `B` 按住时保持 height LOW。
- 只有在 `B` 被按过之后，松开 `B` 才会把 height 切到 HIGH。
- joystick timeout / driver timeout 后回 `[1,0]`，即 height LOW + gripper CLOSE。


### 2026-05-30 v9 实机确认 B 控 gripper，A/X 控 height

- 实机确认 `B` 控 arm gripper：按住 OPEN，松开 CLOSE。
- 实机确认 `A` 控 height LOW。
- 实机确认 `X` 控 height HIGH。
- 启动和 timeout 默认仍为 `[1,0]`：height LOW + gripper CLOSE。


### 2026-05-30 v10 实机确认 relay 顺序为 height/gripper

- 实机确认 relay command 顺序为 `[height_state, gripper_state]`。
- 启动和 timeout 默认改为 `[0,1]`：height LOW + gripper CLOSE。
- `B` 只改变第二位 gripper：按住 OPEN，松开 CLOSE。
- `A/X` 只改变第一位 height：A LOW，X HIGH。

## 适用范围

本 package 目前在正式系統中只負責 STAFF pneumatic joystick bridge：把 STAFF mode 的手柄按鍵轉成 `/pneumatic_gripper_cmd` 四路 relay command。它不直接打開 Arduino serial port；Arduino serial 由 `kfs_staff_gripper_arduino_node` 統一管理。

舊 `pneumatic_relay_driver_node` 仍保留在 package 中，僅作二路 relay standalone 歷史測試或回溯用途；不要和 `kfs_staff_gripper_arduino_node` 同時打開同一個 Arduino。

## Nodes

### pneumatic_relay_driver_node（legacy standalone，当前 start base 不启动）

职责：

```text
ROS2 Int32MultiArray command
  -> USB Serial
  -> Arduino list command string
```

订阅：

```text
/pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray
data[0] = height state, 0 LOW, 1 HIGH
data[1] = gripper state, 0 OPEN, 1 CLOSE
```

发布：

```text
/pneumatic_gripper_status std_msgs/msg/String
```

参数：

```text
serial_port = /dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0
baud_rate = 9600
serial_timeout_sec = 0.1
command_timeout_sec = 0.5
watchdog_hz = 20.0
reconnect_sec = 1.0
safe_state = [0, 1]
```

### pneumatic_gripper_joystick_bridge_node

职责：

```text
/joystick_data
  -> button mapping
  -> /pneumatic_gripper_cmd
```

控制映射：

```text
B: hold arm gripper OPEN, release to CLOSE
A: latch arm height LOW
X: latch arm height HIGH
```

参数：

```text
initial_height_state = 0
publish_hz = 20.0
input_timeout_sec = 0.3
```

## 超时保护

### pneumatic_gripper_joystick_bridge_node（当前正式路径）

触发条件：

```text
/joystick_data 超过 input_timeout_sec = 0.3 s 未更新
或 /operation_mode 不是 STAFF / mode_timeout_sec = 0.5 s 失效
```

行为：

```text
joystick timeout -> /pneumatic_gripper_cmd 回到 safe_state [1,0,1,0]
mode 不是 STAFF 或 mode timeout -> 忽略新按键，不接受新的 relay toggle
```

`/pneumatic_gripper_cmd` 四路顺序固定为：

```text
[M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

### pneumatic_relay_driver_node（legacy standalone）

该 node 是旧二路 serial driver，当前 `r1_start_base_1_0.sh` 不启动。正式五路 Arduino serial timeout 请看 `src/kfs_staff_gripper/README.md`。

## 最小测试

正式測試請先啟動完整系統：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./r1_start_base_1_0.sh
```

觀察 STAFF pneumatic bridge 和 Arduino aggregator：

```bash
ros2 topic echo /operation_mode
ros2 topic echo /view_orientation
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

只測本 package 的 bridge 時，要另外提供 `/joystick_data` 和 `/operation_mode=1`，否則 node 會因 mode gate 或 input timeout 回到 safe/invalid 狀態。

## 调试

确认 Arduino 串口：

```bash
ls -l /dev/serial/by-id/
```

当前确认：

```text
/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0 -> /dev/ttyUSB0
```

注意不要使用 `/dev/ttyACM0`，它当前是达妙 USB-CAN。

## 2026-06-10 v11 arm height 单键切换

当前手柄映射更新为：

```text
B: 按住 arm gripper OPEN，松开 CLOSE
A: 每次按下在 height LOW/HIGH 之间切换
X: 不再用于 arm height，可供其他机构使用
```

切换只在按钮从松开变为按下的瞬间执行一次，长按 `A` 不会按 joystick 发布频率反复切换。bridge 仍以 `20 Hz` 发布 `[height_state, gripper_state]`，Arduino serial 协议和 relay 顺序不变：

```text
[0, 1] = height LOW + gripper CLOSE
[1, 1] = height HIGH + gripper CLOSE
```

新增参数：

```text
height_toggle_button = a
```

可在启动时改成其他 `Joystick` 消息按钮名。超过 `input_timeout_sec = 0.3 s` 未收到 `/joystick_data` 时，bridge 回到安全状态 `[0, 1]`，并要求按钮先松开，之后再次按下才允许切换。

## 2026-06-10 v12 arm gripper 单键锁定与默认 OPEN

本节取代旧版本中 `B` 按住控制和 arm gripper 默认 CLOSE 的当前行为说明；旧内容仅保留为历史记录。

当前手柄映射：

```text
A: 每次按下切换 arm height LOW/HIGH
B: 每次按下切换 arm gripper OPEN/CLOSE
X: 未分配给 arm pneumatic
```

启动默认状态和 `/joystick_data` 超时状态均为：

```text
[height_state, gripper_state] = [0, 0]
height LOW + arm gripper OPEN
```

A、B 都只在按钮上升沿切换，长按不会重复动作。启动或超过
`input_timeout_sec = 0.3 s` 未收到手柄数据后，A、B 必须先松开再重新按下，避免恢复通信时误切换。

正式启动脚本使用 `kfs_staff_gripper_arduino_node` 管理三路 Arduino relay；其完整默认串口状态为：

```text
[0, 0, 0] = arm LOW + arm OPEN + KFS CLOSE
```

standalone `pneumatic_relay_driver_node` 的默认 `safe_state` 同步改为 `[0, 0]`。注意：arm gripper 在手柄超时、节点重启、串口重连和正常关闭时都会回到 OPEN，可能释放正在夹持的物体，这是当前确认的预期行为。


## 2026-06-13 v13 Motor7/8 双 arm 气动选择控制

本节取代 v12 的单 arm 当前说明。bridge 不直接处理 `START`，而是订阅既有
`/motor_position_selector_status`，确保电机位置控制和气动控制使用同一个 Motor7/8 选择。

当前按钮：

```text
START/+ : 切换 Motor7 / Motor8（由 motor selector node 处理）
A       : 切换当前所选 arm height
B       : 切换当前所选 arm gripper
SELECT/-: 仅选中 Motor8 时切换 inclination height
```

`/pneumatic_gripper_cmd` 数据顺序：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper]
```

默认和 `/joystick_data` 超时安全值：

```text
[0,1,0,1,1]
M7 height LOW + gripper OPEN
M8 inclination LOW + height LOW + gripper OPEN
```

Motor8 height 的电磁阀逻辑与 Motor7 相反，因此 Motor8 LOW=`1`。Motor7、Motor8 分别保存
自己的锁定状态，切换选择不会改变未选中 arm。SELECT 在 Motor7 被选中时不执行动作；如果
切换期间一直按住 SELECT，也不会在进入 Motor8 时产生误触发。

参数：

| 参数 | 默认值 | 作用 |
|---|---|---|
| `default_motor_id` | `7` | selector status 到达前的默认 arm |
| `height_toggle_button` | `a` | 所选 arm 高度切换 |
| `gripper_toggle_button` | `b` | 所选 arm 夹爪切换 |
| `inclination_toggle_button` | `select` | Motor8 inclination 切换 |
| `safe_state` | `[0,1,0,1,1]` | 启动与手柄超时安全值 |
| `input_timeout_sec` | `0.3` | 手柄输入超时，单位秒 |
| `publish_hz` | `20.0` | command 刷新频率，单位 Hz |

超时后全部 arm relay 回到 `safe_state`，并要求 A/B/SELECT 先松开再接受下一次上升沿。

## 2026-06-18 v14 七路 Arduino panel 相容性說明（歷史過渡記錄，已由 v15 取代）

`pneumatic_gripper_joystick_bridge_node` 目前仍只負責兩個 arm 的 5 路氣動狀態，輸出 topic
不變：

```text
/pneumatic_gripper_cmd = [M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper]
```

新 Arduino sketch 已升級為 7 路 relay，但 7 路 serial 格式由
`kfs_staff_gripper_arduino_node` 負責合併與輸出。本 package 不直接打開 Arduino serial，也不需要
把 `/pneumatic_gripper_cmd` 改成 7 路。

目前合併後的完整 relay 順序在 `kfs_staff_gripper` package 中維護：

```text
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, reserved]
```

因此本 bridge 的按鍵、timeout、selector 行為均保持不變。Relay 7 / Pin 28 暫時 reserved，
不由 A/B/SELECT/START 或任何現有手柄按鍵控制。

## 2026-06-18 v15 Motor7 inclination 加入 arm command

本節取代 v14 中「Relay 7 reserved」的目前行為說明。Relay 7 / Pin 28 現在用作 Motor7
inclination，因此本 bridge 的 `/pneumatic_gripper_cmd` 從 5 路擴為 6 路：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

默認和 `/joystick_data` 超時安全值為：

```text
[0,1,0,1,1,0]
M7 height LOW + gripper OPEN + inclination LOW
M8 inclination LOW + height LOW + gripper OPEN
```

目前按鍵：

```text
START/+ : 切換 Motor7 / Motor8（由 motor selector node 處理）
A       : 切換目前選中 arm height
B       : 切換目前選中 arm gripper
SELECT/-: 切換目前選中 arm inclination
```

注意：M7 inclination 位於 command 最後一位，但在 Arduino 實體 relay 上是 relay7 / pin28。
M8 inclination 仍是 command 第三位，對應 relay4 / pin25。


## 2026-06-19 Pneumatic keymap transition notes（historical）

本段原本包含 2026-06-19 當天多次 pneumatic 鍵位迭代：六路 command、A/Y height、Y/A gripper relay、L1/R1 inclination 等。這些都已被後面的 `2026-06-19 現行手柄鍵位總表` 和 `2026-06-19 arduino_pneumatic_driver 現行五路 STAFF relay` 取代。

目前 source-truth：

```text
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
STAFF normal: B=M7 gripper, Y=M8 gripper, R3/P1=M7 inclination, L3/P2=M8 inclination
STAFF D-pad down: Motor7/Motor8 relay controls swap
safe_state = [1,0,1,0]
```

## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 arduino_pneumatic_driver 現行五路 STAFF relay

`pneumatic_gripper_joystick_bridge_node` 現在只輸出四路 STAFF arm relay，topic 順序固定為：

```text
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

STAFF mode 按鍵：`B -> M7 gripper`，`Y -> M8 gripper`，`R3/P1 -> M7 inclination/head`，`L3/P2 -> M8 inclination/head`。`A/X` 不在本 node 切 relay；它們由 `r1_arm_control` 的 position bridge 控制 Motor7/Motor8 preset。

安全值為 `[1,0,1,0]`。`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時回到安全值；`/operation_mode` 不是 STAFF 或超過 `mode_timeout_sec=0.5 s` 時忽略新按鍵，但不因切 mode 立即改變已保持的 relay 狀態。

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

## 2026-06-20 Archived Previous README Content - arduino-pneumatic-driver

以下內容是本次 source-verified 文檔同步前已存在的 README 段落。它們已被前面的 current/source-verified 段落取代，只保留作版本回溯與排錯依據，不代表目前實機操作。

<details><summary>Archived section 1</summary>

## 2026-06-18 v15 目前正式狀態摘要

目前正式 `/pneumatic_gripper_cmd` 為 6 路：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

`SELECT/-` 控制目前由 `START/+` 選中的 arm inclination。Motor7 inclination 對應 Arduino relay7 / pin28；Motor8 inclination 對應 relay4 / pin25。舊 v14「relay7 reserved」段落只保留作歷史過渡記錄。

Arduino Mega pneumatic relay gripper driver。此 package 通过 USB Serial 连接 Arduino Mega，并复用已测试的 Arduino 协议：

```text
[0,0]
[1,1]
[0,1]
[1,0]
```

Arduino 侧定义：

```text
Relay 1: arm gripper open/close
  0 = gripper OPEN
  1 = gripper CLOSE

Relay 2: arm gripper height
  0 = height LOW
  1 = height HIGH
```

</details>

<details><summary>Archived section 2</summary>

## 适用范围

本 package 适用于 Arduino Mega + USB Serial + 2 路 relay / solenoid valve 的 pneumatic gripper。它不绑定某一年比赛流程，也不包含战术状态机。

</details>

<details><summary>Archived section 3</summary>

## 超时保护

`pneumatic_relay_driver_node` 实现 command timeout。

触发条件：

```text
超过 command_timeout_sec 没有收到 /pneumatic_gripper_cmd
```

默认值：

```text
command_timeout_sec = 0.5 s
```

超时行为：

```text
向 Arduino 发送 safe_state
默认启动 safe_state = [0,1] = LOW + CLOSE
```

当前 bridge 默认和 timeout 状态是 `[1,0]`，即 height LOW + gripper CLOSE。B 按住 OPEN、松开 CLOSE。A 锁定 height LOW，X 锁定 height HIGH。

`pneumatic_gripper_joystick_bridge_node` 也有 `/joystick_data` 输入 timeout。超过 `input_timeout_sec = 0.3 s` 后，bridge 会回到 `[1,0]`，即 height LOW + gripper CLOSE。

</details>

<details><summary>Archived section 4</summary>

## 最小测试

启动 driver：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
ros2 run arduino_pneumatic_driver pneumatic_relay_driver_node
```

另一个 terminal：

```bash
source install/setup.bash
ros2 topic pub /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0, 0]}" --once
ros2 topic pub /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 1]}" --once
ros2 topic echo /pneumatic_gripper_status
```

</details>

<details><summary>Archived section 5</summary>

## 2026-06-19 STAFF/KFS operation mode pneumatic 鍵位

本節取代前文「A/B/SELECT 作用於目前 selected arm」的現行行為；舊內容保留作歷史記錄。

`pneumatic_gripper_joystick_bridge_node` 現在訂閱 `/operation_mode`。只有 `/operation_mode=1` (STAFF) 且 mode topic 未超過 `mode_timeout_sec=0.5 s` 時才接受按鍵。

STAFF mode 下六路 `/pneumatic_gripper_cmd` 仍為：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

目前鍵位：

```text
A  -> Motor7 height toggle
Y  -> Motor8 height toggle
R1 -> Motor7 inclination / head toggle
L1 -> Motor8 inclination / head toggle
```

`X/B/L2/R2` 不由本 node 使用，已交給 Motor7/8 position bridge。`SELECT/START` 不由本 node 使用，已交給 `operation_mode_selector_node`。

Timeout 行為：`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時，發布 `safe_state=[0,1,0,1,1,0]`。mode 切換本身不自動改 relay 狀態，只影響之後按鍵是否被接受。


## 2026-06-19 五路 relay staff pneumatic 鍵位

本節取代前文六路 `/pneumatic_gripper_cmd` 說明。Motor7/Motor8 height relay 已從 Arduino 面板拆除，STAFF mode 不再使用 A/Y 控制 height。

新的 `/pneumatic_gripper_cmd` 長度為 4：

```text
[M7 staff gripper, M8 inclination/head, M8 staff gripper, M7 inclination/head]
```

STAFF mode 鍵位：

```text
B  -> Motor7 staff gripper relay toggle
X  -> Motor8 staff gripper relay toggle
R1 -> Motor7 inclination/head relay toggle
L1 -> Motor8 inclination/head relay toggle
```

`A` 在 STAFF mode 暫不使用；`Y` 在 STAFF mode 不再控制 height，避免和 KFS mode 的 KFS gripper 混淆。`X/B` 同時仍會送到 Motor7/8 position bridge 作 staff gripper preset/open-close cycle。

Timeout 行為：`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時，發布 `safe_state=[1,0,1,0]`。


## 2026-06-19 STAFF gripper relay 改為 A/Y

本節取代前文 `X/B` 控 staff gripper relay 的說明。

五路 relay 順序仍為：

```text
[KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

STAFF mode 最新 gripper relay 鍵位：

```text
Y -> Motor7 gripper relay toggle
A -> Motor8 gripper relay toggle
```

這兩個鍵同時也送到 `motor_position_selector_joystick_bridge_node`，用於 Motor7/Motor8 的 preset / left-right 90-degree cycle。

`B` 不再由本 node 使用；`X` 目前也不再由本 node 使用。`L1/R1` 不再控制 inclination relay，因為它們已改為 Motor8/Motor7 trim negative。兩個 inclination relay 會保持 safe state，等待後續需要時再分配鍵位。


## 2026-06-19 STAFF head relay moved to L3/R3

本節取代前文「inclination relay 保持 safe state」的說明。

STAFF mode 五路 relay 鍵位現在為：

```text
Y  -> Motor7 gripper relay toggle
A  -> Motor8 gripper relay toggle
R3 -> Motor7 inclination/head relay toggle
L3 -> Motor8 inclination/head relay toggle
```

`L1/R1/L2/R2` 仍保留給 Motor7/8 position manual trim，不再控制 relay。


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


## 2026-06-19 Final STAFF ABXY Layout

最新 STAFF mode ABXY：

```text
A -> Motor7 左右 90° / preset cycle only
X -> Motor8 左右 90° / preset cycle only
B -> Motor7 staff gripper relay toggle only
Y -> Motor8 staff gripper relay toggle only
```

其他 STAFF 鍵位不變：`R1/R2=Motor7 微調`，`L1/L2=Motor8 微調`，`R3=Motor7 抬頭`，`L3=Motor8 抬頭`。

KFS mode 不變：`Y=KFS gripper`，`L2/R2=horizontal positive/negative`，`L1/R1=elevator negative/positive`。

</details>

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
