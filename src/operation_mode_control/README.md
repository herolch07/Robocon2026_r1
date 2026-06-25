> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# operation_mode_control

## 2026-06-19 初始設計

`operation_mode_control` 提供 R1 機構操作模式選擇，不直接控制任何 motor 或 relay。

### 適用範圍

適用於需要把同一個手柄按鍵分成多個機構操作模式的 ROS2 robot。此 package 不綁定單一年份戰術流程，只提供 STAFF/KFS 兩種操作模式 topic。

### Node

#### operation_mode_selector_node

訂閱：

| Topic | Type | 說明 |
|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | 手柄按鍵輸入 |

發布：

| Topic | Type | 說明 | 頻率 |
|---|---|---|---:|
| `/operation_mode` | `std_msgs/msg/Int32` | `0=INVALID, 1=STAFF, 2=KFS` | `publish_hz` |

參數：

| 參數 | 預設值 | 單位 | 作用 |
|---|---:|---|---|
| `staff_button` | `select` | - | 切到 STAFF mode 的按鍵 |
| `kfs_button` | `start` | - | 切到 KFS mode 的按鍵 |
| `default_mode` | `1` | - | joystick 有效後的初始 mode |
| `publish_hz` | `10.0` | Hz | `/operation_mode` 發布頻率 |
| `input_timeout_sec` | `0.5` | s | 多久沒收到 joystick 後發布 INVALID |

### Timeout / Watchdog

若超過 `input_timeout_sec` 沒有收到 `/joystick_data`，node 發布 `/operation_mode=0`。下游 mechanism bridge 收到 `0` 或 mode timeout 時必須忽略機構按鍵，避免手柄資料鏈路失效後沿用舊 mode。

### 最小啟動

```bash
ros2 run operation_mode_control operation_mode_selector_node
ros2 topic echo /operation_mode
```

### 現行按鍵

```text
SELECT / 中左 = STAFF mode
START  / 中右 = KFS mode
```

底盤左搖桿、右搖桿與 D-pad KFS 視角不受 `/operation_mode` 影響。


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

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 mode 與 zone 操作策略

目前不新增 Zone3 自動策略 node。`operation_mode_selector_node` 只提供兩個可組合模式：`SELECT=STAFF`、`START=KFS`。Zone1 使用 STAFF mode，Zone2 使用 KFS mode，Zone3 由機手按 SELECT/START 手動切換需要的機構組。

這個 package 不包含比賽流程或戰術 FSM，因此仍符合「模式選擇可復用、上層策略外置」的 package 邊界。

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

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
