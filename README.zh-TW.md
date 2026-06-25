> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# Robocon R1 ROS 2 工作區

[English](README.md) | [简体中文](README.zh-CN.md) | 繁體中文

本倉庫是 EdUHK Robotics Team @ Hero 開發的目前 R1 機器人控制工作區。

- GitHub：`herolch07`
- 目前最終操作指南：[r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md)
- 系統架構說明：[ARCHITECTURE.md](ARCHITECTURE.md)
- Node/topic 圖：[NODE_GRAPH.md](NODE_GRAPH.md)
- 底盤速度調參說明：[SPEED_TUNING.md](SPEED_TUNING.md)
- 目前完整啟動腳本：`./r1_start_base_1_0.sh`
- 專案記錄中的目前實機確認日期：2026-05-22

## 目前系統

這個工作區是 Robocon R1 的 ROS 2 控制系統，包含：

- Motor 1-4：四輪全向底盤，VEL 模式
- Motor 5：KFS 升降機構，VEL 模式
- Motor 6：KFS 水平移動機構，VEL 模式
- Motor 7：STAFF gripper 位置馬達，POS_VEL 模式
- Motor 8：STAFF gripper 位置馬達，POS_VEL 模式
- Arduino 五路氣動 relay panel：KFS gripper、M7/M8 staff gripper、M7/M8 inclination/head relay
- 8BitDo 手掣輸入，底層使用 Linux `evdev`
- 可選鍵盤遙控 package 只保留作舊低速調試；目前比賽操作使用手掣

## 手掣映射

```text
永遠生效：
  左搖桿：人視角底盤平移
  右搖桿：底盤原地旋轉
  D-pad：設定 KFS visual front 在人視角中的方向
  X + Y + B + A 長按 5 秒：Raspberry Pi shutdown command

模式切換：
  SELECT / 中左：STAFF mode (/operation_mode = 1)
  START / 中右：KFS mode (/operation_mode = 2)

STAFF mode：
  A：Motor7 90° / preset cycle
  X：Motor8 90° / preset cycle
  B：Motor7 staff gripper relay toggle
  Y：Motor8 staff gripper relay toggle
  R1/R2：Motor7 微調 負/正
  L1/L2：Motor8 微調 負/正
  R3/P1：Motor7 inclination/head relay toggle
  L3/P2：Motor8 inclination/head relay toggle

KFS mode：
  Y：KFS gripper toggle
  L2/R2：Motor6 horizontal 正向(out)/負向(in)
  L1/R1：Motor5 elevator 負向(down)/正向(up)
```

## 目前重要預設值

```text
手掣搖桿範圍：-512 .. 512
扳機範圍：0 .. 512
手掣死區：15
joystick_bridge max_speed_cm：150.0
joystick_bridge max_rotation：3.0
joystick_bridge translation_linear_weight：0.1
joystick_bridge rotation_linear_weight：0.1
local_navigation_node max_wheel_speed_rad_s：40.0
local_navigation_node max_wheel_accel_rad_s2：25.0
local_navigation_node accel_limit_mode：per_wheel
damiao_node motor_ids：[1,2,3,4,5,6,7,8]
damiao_node position_mode_motor_ids：[7,8]
damiao_node command_timeout_sec：0.5
Motor7/Motor8 位置點：[0.0, 32.0, -32.0] rad
STAFF pneumatic safe_state：[1,0,1,0]
Arduino 五路 safe_state：[0,1,0,1,0]
```

底盤運動學預設值：

```text
Motor 1 = 左前
Motor 2 = 右前
Motor 3 = 右後
Motor 4 = 左後

lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4 = [1, 1, -1, -1]
lateral_coeff_1..4 = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

## 快速啟動

在機器人主機上執行：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --symlink-install
source install/setup.bash
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

腳本會啟動 tmux session：

```text
r1_control
```

常用 tmux 命令：

```text
重新進入：tmux attach -t r1_control
離開但保持運行：Ctrl+b，然後按 d
關閉全部：tmux kill-session -t r1_control
```

## Package 一覽

```text
src/my_joystick_msgs          自訂 Joystick 訊息
src/my_joystick_driver        evdev 手掣驅動，發布 /joystick_data
src/joystick_bridge           手掣到底盤 /local_driving 的橋接
src/base_omniwheel_r2_700     全向底盤運動學與達妙馬達驅動
src/r1_arm_control            Motor 5/6 速度控制與 Motor 7/8 POS_VEL 控制
src/kfs_staff_gripper         KFS/STAFF 五路 Arduino relay aggregator
src/arduino_pneumatic_driver  Arduino relay 氣動夾爪 joystick bridge
src/keyboard_teleop           鍵盤低速調試遙控
```

## 安全保護

目前控制鏈有多層 watchdog：

- `joystick_bridge`：`/joystick_data` 超時後發布 `/local_driving = [0, 0, 0]`。
- `local_navigation_node`：`/local_driving` 超時後讓 Motor 1-4 歸零。
- `damiao_node`：連續 VEL 命令超時後只讓對應馬達歸零。
- `r1_arm_control` controllers：對應 speed command 超時後執行機構速度歸零。
- `arduino_pneumatic_driver`：STAFF bridge 在 joystick timeout 後回到 `/pneumatic_gripper_cmd=[1,0,1,0]`；`kfs_staff_gripper_arduino_node` 擁有 Arduino serial，啟動/重連/關閉時套用完整五路 `safe_state=[0,1,0,1,0]`。

## 舊文件說明

本工作區裡有一些歷史報告。如果某段內容提到 `±8192`、`410` 手掣死區、`100 cm/s` 預設底盤速度、`start_all_nodes.sh`、`start_full_control_chain.sh`、VESC 節點，或舊路徑 `Robocon2026_r2/2026R2_ws`，除非該段明確標成目前狀態，否則應視為舊版記錄。

目前操作以本 README 和 [r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md) 為準。

## ROS2 網絡隔離

R1 啟動腳本預設使用獨立 ROS2 環境：

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

這樣可以避免 R1 發現 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control` 等 node/topic。修改前請先閱讀 `ROS_DOMAIN_ISOLATION.md`。

## 達妙馬達急停自動恢復

Motor 1-8 回饋逾時或失能後，driver 每 2 秒自動發送對應模式的 enable/safe command，並阻止非零命令。收到已使能回饋且手掣回中一次後才恢復運動。監控 `/damiao_motor_status`：`0=RECOVERING`、`1=WAIT_NEUTRAL`、`2=READY`、`3=DISABLED`。


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
L3：+10 rad/s
R3：-10 rad/s
L3 + R3 或全部鬆開：0 rad/s
```

監控目前視角：

```bash
ros2 topic echo /view_orientation
```

## 2026-06-16 8BitDo P1／P2 背鍵配置

P1／P2 目前不是 ROS 內的獨立按鍵。`evtest` 實測 A/B/X/Y 有事件，但 P1／P2 沒有獨立
事件，因此目前不修改 `Joystick.msg`、`joystick_node.py` 或任何 bridge node。

目前使用 8BitDo 軟體 remap：

```text
P1 = R3
P2 = L3
```

實際效果：

```text
P1 -> R3 -> Motor6 -10 rad/s
P2 -> L3 -> Motor6 +10 rad/s
P1 + P2 或全部鬆開 -> Motor6 0 rad/s
```

這只改變手柄物理操作位置，不改變 ROS topic、message、timeout 或控制計算。

本功能已於 2026-06-15 完成實機測試並確認繼續採用。

## 2026-06-18 七路 relay 操作更新歷史記錄（已被五路 relay 取代）

本節保留 2026-06-18 臨時七路 relay / 六值 `/pneumatic_gripper_cmd` 設計，不再是目前 source-truth runtime。現行正式 Arduino 五路 relay 為：

```text
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
/kfs_staff_gripper_cmd = [KFS gripper]
```

手柄內部 remap 仍有效：`P1=R3`、`P2=L3`，目前在 STAFF mode 用於 Motor7/Motor8 inclination/head relay。controller-gated autostart 也仍有效：`systemd/r1-control-autostart.service` 可啟動 `scripts/wait_and_start_robot.sh`，等 8BitDo / Xbox controller active 後自動執行 `r1_start_base_1_0.sh`。

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

## 2026-06-20 Archived Previous README Content - root-2026-06-18

以下內容是本次 source-verified 文檔同步前已存在的 README 段落。它們已被前面的 current/source-verified 段落取代，只保留作版本回溯與排錯依據，不代表目前實機操作。

<details><summary>Archived section 1</summary>

## 2026-06-18 目前正式操作更新

本節為目前最新操作摘要，取代前文所有舊版按鍵方向、relay7 reserved、以及手動啟動優先的說明；舊段落保留作版本回溯。

```text
P1 = R3 -> STAFF mode Motor7 inclination/head relay
P2 = L3 -> STAFF mode Motor8 inclination/head relay
P1 + P2 或全部鬆開 -> Motor6 0 rad/s
```

七路 Arduino relay 目前順序：

```text
[relay1, relay2, relay3, relay4, relay5, relay6, relay7]
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

`/pneumatic_gripper_cmd` 目前為 6 個值：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

`SELECT/-` 會控制目前由 `START/+` 選中的 arm inclination：選中 Motor7 時控制 relay7 / Motor7 inclination；選中 Motor8 時控制 relay4 / Motor8 inclination。

新增 controller-gated autostart：Pi 開機後可由 `systemd/r1-control-autostart.service` 啟動 `scripts/wait_and_start_robot.sh`，等 8BitDo / Xbox controller active 後才自動執行 `r1_start_base_1_0.sh`。預設 `STOP_ON_CONTROLLER_LOST=0`，手柄中途關掉不自動 kill 整套 ROS，仍依靠各 node watchdog 進安全輸出。

</details>

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
