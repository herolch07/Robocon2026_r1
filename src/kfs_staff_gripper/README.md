> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# kfs_staff_gripper


## 2026-06-20 Source-Verified Current State

目前 source code 的正式 Arduino relay 順序為五路：

```text
relayPins = {22, 24, 25, 27, 28}
serial command = [r1,r2,r3,r4,r5]
HIGH = ON, LOW = OFF
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
full safe_state = [0,1,0,1,0]
```

`/pneumatic_gripper_cmd` 必須是 4 路並映射到 relay2-5；`/kfs_staff_gripper_cmd` 是 1 路並映射到 relay1。舊三路、六路、七路段落只保留作硬件演進記錄，不代表目前實機 wiring。

KFS/STAFF pneumatic 的 Arduino Mega 五路 relay 控制 package。

## 更新记录 / Changelog

### v0.3.5 Arduino serial auto-detect（2026-06-07）

- 换 Arduino Mega 后，官方 Mega 的 by-id 路径可能从旧 CH340 `usb-1a86...` 变成 `usb-Arduino__www.arduino.cc__0042...`。
- `kfs_staff_gripper_arduino_node` 现在会优先使用 `serial_port` 参数；如果该路径不存在，会自动扫描 `/dev/serial/by-id/` 中的 Arduino/CH340 路径，并排除达妙 USB-CAN `HDSC`。
- 如果 Arduino IDE Serial Monitor 正在占用串口，ROS node 仍然无法打开，需要先关闭 Serial Monitor。

### v0.3.4 arm relay 顺序实机确认（2026-05-30）

- arm pneumatic 在三路 aggregator 中的 relay 顺序为 `[height_state, gripper_state]`。
- 完整 safe state 改为 `[0,1,0]`：arm height LOW + arm gripper CLOSE + KFS CLOSE。

### v0.3.3 arm pneumatic 实机按键确认（2026-05-30）

- `B` 控 arm gripper：按住 OPEN，松开 CLOSE。
- `A` 控 arm height LOW。
- `X` 控 arm height HIGH。
- aggregator `safe_state` 保持 `[0,1,0]`：arm height LOW + arm CLOSE + KFS CLOSE。

### v0.3.2 arm height 启动默认 LOW（2026-05-30）

- aggregator 默认 `safe_state` 改为 `[0,1,0]`：arm gripper CLOSE + arm height LOW + KFS staff gripper CLOSE。
- 启动 `r1_start_base_1_0.sh` 后 arm height 默认保持 LOW。
- `B` 控 arm gripper，按住 OPEN、松开 CLOSE；`A` 控 height LOW；`X` 控 height HIGH。

### v0.3.1 arm pneumatic 新接线 safe state（2026-05-30，历史记录，已被 v0.3.3 覆盖）

- arm pneumatic 的 `/pneumatic_gripper_cmd` 当前语义为 `[arm_gripper_state, arm_height_state]`。
- 当时假设 `A/X` 控 gripper、`B` 控 height；v0.3.3 后实机确认该假设错误。
- v0.3.1 曾把 aggregator 默认 `safe_state` 改为 `[1,1,0]`；v0.3.2 后曾按当时假设改为 `[1,0,0]`；v0.3.4 实机确认 relay 顺序后改为 `[0,1,0]`。
- KFS staff gripper 仍由 `Y` 控制，按住 OPEN，松开 CLOSE。

### v0.3.0 三路 relay sketch 适配（2026-05-29）

- Arduino sketch 已改为三路 relay：D8/D9/D10。
- 三路 relay 均为高电平触发：`HIGH = ON`，`LOW = OFF`。
- Arduino serial command 改为 `[r1,r2,r3]`，例如 `[1,0,1]`。
- relay 1-2 继续给 arm pneumatic 使用，对应 `/pneumatic_gripper_cmd`。
- relay 3 给 KFS staff gripper 使用，对应 `/kfs_staff_gripper_cmd = [staff_gripper_state]`。
- controller 只使用 `Y` 控制 KFS：按住 `Y` OPEN，松开 CLOSE。
- `R3` 当前不再由 KFS staff gripper node 使用。
- ROS 侧 KFS v0.3.0 初始 safe/default state 曾为 `[0,0,0]`；v0.3.1 后因 arm pneumatic 新接线改为 `[1,1,0]`。

### v0.2.0 实机按键确认（2026-05-28，历史记录，已被 v0.3.0 覆盖）

- 实机确认 `Y` 为 KFS staff gripper 有效控制：按住 OPEN，松开 CLOSE。
- 当前 safe/default state 为 `[0, 0]`，实机表现为 staff gripper CLOSE。
- 当时 `R3` 对应 staff relay 4 channel；v0.3.0 后 Arduino 改为三路 relay，R3 不再使用。

### v0.1.0 初始版本（2026-05-25）

- 新增 `kfs_staff_gripper_arduino_node`
- 新增 `kfs_staff_gripper_joystick_bridge_node`
- 支持同一个 Arduino Mega 上同时管理：
  - 原本 arm pneumatic 的 relay 1-2
  - KFS staff gripper 的 relay 3
- 实现 serial reconnect、command timeout、shutdown safe state
- 保留与现有 `/pneumatic_gripper_cmd` 的兼容，不需要修改原本 `pneumatic_gripper_joystick_bridge_node`

## Package 用途与适用范围

本 package 适用于 Arduino Mega + 五路 relay board + KFS gripper + 雙 STAFF gripper/inclination pneumatic 结构。
它只负责 relay 输出与手柄到 staff gripper command 的桥接，不包含比赛策略、自动流程或年份绑定逻辑。

重要限制：如果 KFS staff gripper 和 arm pneumatic 接在同一个 Arduino Mega 上，运行本 package 时不要再同时运行旧的 `pneumatic_relay_driver_node`，否则两个 node 会抢同一个 serial port。

推荐运行方式：

```text
pneumatic_gripper_joystick_bridge_node  -> /pneumatic_gripper_cmd
kfs_staff_gripper_joystick_bridge_node  -> /kfs_staff_gripper_cmd
kfs_staff_gripper_arduino_node          -> Arduino serial [r1,r2,r3,r4,r5]
```

## Node 列表

### `kfs_staff_gripper_arduino_node`

职责：统一打开 Arduino Mega serial port，并把 STAFF pneumatic 与 KFS gripper 的 relay 状态合并成五路 Arduino command。

订阅：

| Topic | Type | 含义 | 频率 |
|---|---|---|---|
| `/pneumatic_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | STAFF 四路状态 `[M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，默认映射到 relay 2-5 | 约 20 Hz |
| `/kfs_staff_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | KFS gripper 单路状态，默认映射到 relay 1 | 约 20 Hz |

发布：

| Topic | Type | 含义 |
|---|---|---|
| `/kfs_staff_gripper_status` | `std_msgs/msg/String` | serial 连接状态、发送内容、Arduino 回传日志 |

参数：

| 参数 | 默认值 | 单位 | 作用 |
|---|---:|---|---|
| `serial_port` | `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0` | - | 首选 Arduino Mega serial 设备路径；如果不存在，会自动扫描 Arduino/CH340 by-id 路径 |
| `baud_rate` | `9600` | baud | 必须与 Arduino sketch `Serial.begin(9600)` 一致 |
| `serial_timeout_sec` | `0.1` | s | serial read timeout |
| `command_timeout_sec` | `0.5` | s | 超过此时间未收到新 command 后进入 safe state |
| `watchdog_hz` | `20.0` | Hz | timeout/reconnect 检查频率 |
| `reconnect_sec` | `1.0` | s | serial 断开后的重连间隔 |
| `safe_state` | `[0, 1, 0, 1, 0]` | - | 五路安全状态：KFS CLOSE + M7 gripper OPEN + M8 inclination LOW + M8 gripper OPEN + M7 inclination LOW |
| `arm_relay_indices` | `[1, 2, 3, 4]` | - | `/pneumatic_gripper_cmd` 映射到五路 relay 的位置 |
| `staff_relay_indices` | `[0]` | - | `/kfs_staff_gripper_cmd` 映射到 relay 1 的位置 |
| `arm_cmd_topic` | `/pneumatic_gripper_cmd` | - | arm pneumatic command topic |
| `staff_cmd_topic` | `/kfs_staff_gripper_cmd` | - | KFS staff gripper command topic |

Arduino 输出格式：

```text
[relay1,relay2,relay3,relay4,relay5]\n
example: [0,1,0,1,0]
```

### `kfs_staff_gripper_joystick_bridge_node`

职责：把手柄按键转换为 KFS staff gripper 单路 relay command。

订阅：

| Topic | Type | 含义 | 频率 |
|---|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | 手柄输入 | 约 20 Hz |

发布：

| Topic | Type | 含义 | 频率 |
|---|---|---|---|
| `/kfs_staff_gripper_cmd` | `std_msgs/msg/Int32MultiArray` | `[staff_gripper_state]` | 默认 20 Hz |

默认手柄映射（2026-05-28 实机确认）：

```text
Y  : KFS mode 下每按一次切換 KFS gripper OPEN/CLOSE
R3 : 不由本 node 使用
```

实机状态约定：

```text
/kfs_staff_gripper_cmd = [0] -> staff gripper CLOSE
/kfs_staff_gripper_cmd = [1] -> staff gripper OPEN
```

参数：

| 参数 | 默认值 | 单位 | 作用 |
|---|---:|---|---|
| `staff_button` | `y` | - | 控制 KFS staff gripper open/close 的按键字段名 |
| `publish_hz` | `20.0` | Hz | command 发布频率 |
| `input_timeout_sec` | `0.3` | s | 手柄输入超时时间 |
| `safe_state` | `[0]` | - | 手柄超时后的 staff gripper 安全状态 |

## 超时与失效保护

### `kfs_staff_gripper_arduino_node`

触发条件：

```text
`/pneumatic_gripper_cmd` 或 `/kfs_staff_gripper_cmd` 任一来源超过 command_timeout_sec = 0.5 s 没有新 command。两个来源独立计时，staff command 持续刷新不会掩盖 arm pneumatic timeout，反过来也一样。
```

默认行为：

```text
只把超时来源负责的 relay indices 写回 safe_state 对应值：
- arm pneumatic timeout：默认 relay 1-2 回 safe
- KFS staff timeout：默认 relay 3 回 safe

如果 serial 断开、重连或 node 关闭，则发送完整 safe_state = [0,1,0]。
```

serial 断开时：

```text
每 reconnect_sec = 1.0 s 尝试重连
重连成功后立即发送 safe_state
```

关闭 ROS node 时：

```text
发送 shutdown_safe_state = safe_state
关闭 serial handle
```

### `kfs_staff_gripper_joystick_bridge_node`

触发条件：

```text
超过 input_timeout_sec = 0.3 s 没有收到 /joystick_data
```

默认行为：

```text
发布 /kfs_staff_gripper_cmd = [0]
staff gripper CLOSE
```

## 启动方式

编译：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --packages-select kfs_staff_gripper --symlink-install
source install/setup.bash
```

只測 KFS relay / 五路 aggregator：

```bash
ros2 run kfs_staff_gripper kfs_staff_gripper_arduino_node
ros2 topic pub --once /kfs_staff_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1]}"
ros2 topic pub --once /kfs_staff_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0]}"
ros2 topic echo /kfs_staff_gripper_status
```

与现有 arm pneumatic 一起运行：

```bash
ros2 run arduino_pneumatic_driver pneumatic_gripper_joystick_bridge_node
ros2 run kfs_staff_gripper kfs_staff_gripper_joystick_bridge_node
ros2 run kfs_staff_gripper kfs_staff_gripper_arduino_node
```

使用 R1 总启动脚本：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./r1_start_base_1_0.sh
```

当前脚本会启动：

```text
relay_panel: kfs_staff_gripper_arduino_node
pneu_bridge: pneumatic_gripper_joystick_bridge_node
kfs_bridge: kfs_staff_gripper_joystick_bridge_node
```


不要同时运行：

```bash
ros2 run arduino_pneumatic_driver pneumatic_relay_driver_node
```

因为它会和 `kfs_staff_gripper_arduino_node` 抢同一个 Arduino serial port。

## 接口约定

- 五路 relay 状态只允许 `0` 或 `1`。
- `kfs_staff_gripper_arduino_node` 内部会把非零值 clamp 成 `1`，零值为 `0`。
- Arduino command 固定为 `[r1,r2,r3,r4,r5]`。
- 默认 relay 编号按 Arduino sketch 数组顺序解释：

```text
relay 1 -> pin 22 -> KFS gripper
relay 2 -> pin 24 -> Motor7 staff gripper
relay 3 -> pin 25 -> Motor8 inclination/head
relay 4 -> pin 27 -> Motor8 staff gripper
relay 5 -> pin 28 -> Motor7 inclination/head
```

## 调试方式与常见问题

查看节点：

```bash
ros2 node list
```

查看 command：

```bash
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

如果 serial 打不开：

```bash
ros2 param get /kfs_staff_gripper_arduino_node serial_port
ls -l /dev/serial/by-id/
ros2 topic echo /kfs_staff_gripper_status
```

换成官方 Arduino Mega 后，正常 by-id 可能类似：

```text
/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_... -> ../../ttyACM0
```

如果 Arduino IDE Serial Monitor 正在打开这个 port，ROS node 会显示打不开串口；先关闭 Serial Monitor 再重启 `relay_panel`。

如果旧 arm pneumatic 不动作：

- 确认没有运行旧 `pneumatic_relay_driver_node`。
- 确认 `pneumatic_gripper_joystick_bridge_node` 仍在发布 `/pneumatic_gripper_cmd`。
- 确认 `arm_relay_indices` 是否和 Arduino 接线一致。

## 你提供的 Arduino code 需要注意的问题

1. 現行 sketch 是五路 relay：`relayPins = {22,24,25,27,28}`，serial 格式必須剛好是 `[1,0,1,0,1]` 這種五值 list。
2. 目前 Arduino code 註釋和實際陣列都表示高電平觸發：`HIGH = Relay ON`，`LOW = Relay OFF`。如果 relay module 類型改變，Arduino 里的 `RELAY_ON/OFF` 要同步修改。
3. Arduino 本身沒有 millis watchdog。如果 ROS 或 USB 斷開，Arduino 會保持最後一次 relay 狀態。本 package 在 ROS 側做 timeout safe state，但 USB 線直接斷開時 Arduino 仍不會自動關 relay；後續建議 Arduino sketch 也加 watchdog。
4. 不能同時運行舊 `pneumatic_relay_driver_node` 和 `kfs_staff_gripper_arduino_node`，否則兩個 ROS serial driver 會搶同一個 Arduino port。

## 2026-06-10 v0.3.6 arm 默认 OPEN、KFS 默认 CLOSE

正式启动脚本中的三路 Arduino aggregator 当前默认状态改为：

```text
safe_state = [0, 0, 0]
relay order = [arm_height, arm_gripper, kfs_gripper]
含义 = arm LOW + arm OPEN + KFS CLOSE
```

当前按钮行为：

```text
A: 每次按下切换 arm height LOW/HIGH
B: 每次按下切换 arm gripper OPEN/CLOSE
Y: 按住 KFS gripper OPEN，松开 KFS gripper CLOSE
X: 未由这两个 gripper bridge 使用
```

KFS bridge 的 `safe_state` 保持 `[0]`，因此 bash 启动、Y 松开、KFS command timeout、Arduino 重连和节点关闭时，KFS gripper 均为 CLOSE。Y 本次没有改成锁定切换。

aggregator 继续对 arm 和 KFS 两个 command topic 独立执行 `command_timeout_sec = 0.5 s` watchdog：arm 来源超时只将 relay 1-2 回到 `[0,0]`；KFS 来源超时只将 relay 3 回到 `0`。

## 2026-06-10 v0.3.7 KFS Y 单键锁定切换

本节取代 v0.3.6 中 Y 按住 OPEN、松开 CLOSE 的当前行为说明；旧内容仅保留为历史记录。

当前按钮行为：

```text
A: 每次按下切换 arm height LOW/HIGH
B: 每次按下切换 arm gripper OPEN/CLOSE
Y: 每次按下切换 KFS gripper OPEN/CLOSE
X: 未由这两个 gripper bridge 使用
```

KFS 启动默认仍为 CLOSE：

```text
/kfs_staff_gripper_cmd = [0] -> CLOSE
/kfs_staff_gripper_cmd = [1] -> OPEN
```

Y 只在按钮从松开变为按下的上升沿切换一次，长按不会反复切换。超过
`input_timeout_sec = 0.3 s` 未收到 `/joystick_data` 时，KFS bridge 回到 `[0] = CLOSE`；恢复通信后必须先松开 Y，再重新按下才能 OPEN。

三路 Arduino aggregator 的完整默认状态保持不变：

```text
[0, 0, 0] = arm LOW + arm OPEN + KFS CLOSE
```

Arduino serial node、串口格式、relay 3 映射和 `command_timeout_sec = 0.5 s` watchdog 均未改变。


## 2026-06-13 v0.4.0 六路 Arduino relay panel

本节取代旧三路 relay 作为当前实现说明；旧章节保留用于设计回溯。正式串口节点仍为
`kfs_staff_gripper_arduino_node`，同一时间不得启动其他节点打开同一个 Arduino 串口。

Arduino 输出顺序固定为：

```text
[relay1, relay2, relay3, relay4, relay5, relay6]
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper]
```

确认的值语义：

| Relay | Pin | 机构 | `0` | `1` |
|---|---:|---|---|---|
| 1 | 22 | KFS gripper | CLOSE | OPEN |
| 2 | 23 | Motor7 arm height | LOW | HIGH |
| 3 | 24 | Motor7 arm gripper | CLOSE | OPEN |
| 4 | 25 | Motor8 inclination | LOW | HIGH |
| 5 | 26 | Motor8 arm height | HIGH | LOW |
| 6 | 27 | Motor8 arm gripper | CLOSE | OPEN |

完整启动、串口重连、节点关闭安全状态为：

```text
safe_state = [0,0,1,0,1,1]
含义 = KFS CLOSE + M7 LOW/OPEN + M8 inclination LOW/height LOW/gripper OPEN
```

订阅接口：

```text
/pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray
  [M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper]
/kfs_staff_gripper_cmd std_msgs/msg/Int32MultiArray
  [KFS gripper]
```

默认映射参数为 `arm_relay_indices=[1,2,3,4,5]`、
`staff_relay_indices=[0]`。节点只接受与映射长度完全相等的 command，旧两位或三位 command
会被拒绝，且不会刷新该来源的 watchdog。两个来源分别超过
`command_timeout_sec=0.5 s` 后，只恢复自己负责的 relay；串口重连和节点关闭恢复完整
`safe_state`。Arduino 严格收到 `[x,x,x,x,x,x]\n`。

## 2026-06-18 v0.4.1 七路 Arduino relay panel（歷史過渡記錄，已由 v0.4.2 取代）

本節取代 v0.4.0 六路 serial 輸出的目前行為說明；舊章節保留作版本回溯。你提供的新
Arduino sketch 使用 7 路 relay，pin 順序為 `22..28`，並且只接受 7 個值的嚴格格式：

```text
[relay1, relay2, relay3, relay4, relay5, relay6, relay7]
example: [0,0,1,0,1,1,0]
```

目前 ROS 上層接口保持不變：

```text
/pneumatic_gripper_cmd = [M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper]
/kfs_staff_gripper_cmd = [KFS gripper]
```

Arduino aggregator 內部合併後輸出 7 路：

| Relay | Pin | 目前用途 | 來源 | Safe |
|---|---:|---|---|---:|
| 1 | 22 | KFS gripper | `/kfs_staff_gripper_cmd[0]` | 0 |
| 2 | 23 | Motor7 arm height | `/pneumatic_gripper_cmd[0]` | 0 |
| 3 | 24 | Motor7 arm gripper | `/pneumatic_gripper_cmd[1]` | 1 |
| 4 | 25 | Motor8 inclination | `/pneumatic_gripper_cmd[2]` | 0 |
| 5 | 26 | Motor8 arm height | `/pneumatic_gripper_cmd[3]` | 1 |
| 6 | 27 | Motor8 arm gripper | `/pneumatic_gripper_cmd[4]` | 1 |
| 7 | 28 | reserved / 未分配 | 無 topic | 0 |

完整啟動、serial 重連、node 關閉安全狀態為：

```text
safe_state = [0,0,1,0,1,1,0]
含義 = KFS CLOSE + M7 LOW/OPEN + M8 inclination LOW/height LOW/gripper OPEN + relay7 OFF
```

`arm_relay_indices` 仍為 `[1,2,3,4,5]`，`staff_relay_indices` 仍為 `[0]`。Relay 7
目前不由任何手柄按鍵控制，也不接受 `/pneumatic_gripper_cmd` 更新。等 pin 28 的實際機構與
安全語義確認後，再新增獨立 topic、映射參數或按鍵邏輯。

超時策略不變：arm topic 超時只恢復 relay 2-6；KFS topic 超時只恢復 relay 1；完整 safe
state 只在啟動、serial 重連與 node 關閉時發送。

## 2026-06-18 v0.4.2 Relay 7 改為 Motor7 inclination

本節取代 v0.4.1 中「relay7 reserved」的目前行為說明；v0.4.1 保留作當時安全過渡記錄。
Relay 7 / Pin 28 現在確認為 Motor7 inclination。

完整 Arduino serial relay 順序為：

```text
[relay1, relay2, relay3, relay4, relay5, relay6, relay7]
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

上層 topic 更新為：

```text
/pneumatic_gripper_cmd = [M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
/kfs_staff_gripper_cmd = [KFS gripper]
```

`arm_relay_indices` 更新為 `[1,2,3,4,5,6]`，所以 6 路 arm command 會映射到 relay 2-7。
完整 safe state 保持：

```text
safe_state = [0,0,1,0,1,1,0]
含義 = KFS CLOSE + M7 height LOW + M7 gripper OPEN + M8 inclination LOW + M8 height LOW + M8 gripper OPEN + M7 inclination LOW
```

手柄行為同步更新：`SELECT` 不再只控制 Motor8 inclination，而是控制「目前選中的 arm」的
inclination。也就是 START 選中 Motor7 時，SELECT 切換 Motor7 inclination；START 選中 Motor8
時，SELECT 切換 Motor8 inclination。A/B 仍控制目前選中 arm 的 height/gripper。


## 2026-06-19 KFS mode gating

`kfs_staff_gripper_joystick_bridge_node` 現在訂閱 `/operation_mode`。只有 `/operation_mode=2` (KFS) 且 mode topic 未超過 `mode_timeout_sec=0.5 s` 時，`Y` 才會切換 KFS gripper。

```text
SELECT / 中左 = STAFF mode，此時 Y 交給 Motor8 staff gripper relay
START  / 中右 = KFS mode，此時 Y 控制 KFS gripper toggle
```

Timeout 行為不變：`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時，KFS gripper 回到 `safe_state=[0]`。mode 切換本身不自動開關 KFS gripper。


## 2026-06-19 五路 Arduino relay 協議

本節取代前文六路／七路 Arduino relay 說明；舊內容保留作硬件演進記錄。

最新 Arduino sketch：

```text
NUM_RELAYS = 5
relayPins = {22, 24, 25, 27, 28}
serial format = [r1,r2,r3,r4,r5]
HIGH = ON, LOW = OFF
```

ROS 端完整 relay 順序：

```text
[ KFS gripper,
  Motor7 staff gripper,
  Motor8 inclination/head,
  Motor8 staff gripper,
  Motor7 inclination/head ]
```

`kfs_staff_gripper_arduino_node` 仍聚合兩個 topic：

```text
/kfs_staff_gripper_cmd -> relay 1，長度 1
/pneumatic_gripper_cmd -> relay 2-5，長度 4
```

預設 safe state：

```text
[0,1,0,1,0]
```

含義：KFS gripper CLOSE；Motor7/Motor8 staff gripper relay 保持 OPEN；兩個 inclination/head relay OFF。

Timeout 行為不變：任一 command topic 超過 `command_timeout_sec=0.5 s` 未更新時，只把該 topic 對應 relay group 恢復到 safe state。


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 kfs_staff_gripper 現行五路 Arduino 聚合

`kfs_staff_gripper_arduino_node` 現在是 Arduino 五路 relay 的 serial 聚合器。它把 `/kfs_staff_gripper_cmd` 與 `/pneumatic_gripper_cmd` 合成 Arduino 需要的 5 位格式：

```text
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

安全狀態為 `[0,1,0,1,0]`。KFS gripper 只在 `/operation_mode=2` 時由 `Y` 切換；STAFF mode 的 `Y` 由 `arduino_pneumatic_driver` 用作 Motor8 staff gripper relay，不會同時控制 KFS gripper。

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

## 2026-06-20 Archived Previous README Content - kfs-staff-gripper

以下內容是本次 source-verified 文檔同步前已存在的 README 段落。它們已被前面的 current/source-verified 段落取代，只保留作版本回溯與排錯依據，不代表目前實機操作。

<details><summary>Archived section 1</summary>

## 接口约定

- 三路 relay 状态只允许 `0` 或 `1`。
- `kfs_staff_gripper_arduino_node` 内部会把非零值 clamp 成 `1`，零值为 `0`。
- Arduino command 固定为 `[r1,r2,r3]`。
- 默认 relay 编号按 Arduino sketch 数组顺序解释：

```text
relay 1 -> pin 8
relay 2 -> pin 9
relay 3 -> pin 10
```

</details>

<details><summary>Archived section 2</summary>

## 你提供的 Arduino code 需要注意的问题

1. 当前 sketch 中 D8/D9/D10 三路均为高电平触发：`HIGH = Relay ON`，`LOW = Relay OFF`。如果后续 relay module 类型改变，Arduino 里的 `RELAY_ON/OFF` 要同步修改。
2. 现在 Arduino 只接受长度刚好为 7 的 `[1,0,1]`，格式很严格。ROS node 已按这个格式发送。
3. Arduino 没有超时保护。如果 ROS 或 USB 断开，Arduino 会保持最后一次 relay 状态。本 package 在 ROS 侧对 arm pneumatic 与 KFS staff gripper 分别做 timeout safe state，但如果 USB 线直接断开，Arduino 仍不会自动关 relay。之后建议把 Arduino sketch 也加 millis watchdog。
4. 如果和旧 pneumatic 共用同一个 Arduino，不能两个 ROS serial driver 同时打开同一个 `/dev/ttyUSB*`。本 package 的 aggregator node 就是为了解决这个问题。

</details>

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
