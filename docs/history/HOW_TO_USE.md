> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# R1 使用說明

本說明面向日常操作。當前完整系統以 `r1_start_base_1_0.sh` 為入口；`start.sh`、`start_background.sh` 只保留為舊底盤 4 節點流程，不建議作為 R1 完整系統首選。

## 2026-06-20 Source-Verified Current How To Use

本節是目前 `HOW_TO_USE.md` 的 source-verified 操作摘要，依據 `r1_start_base_1_0.sh` 和目前 Python nodes。本文後面較早日期段落若描述 START 選 Motor7/8、A/Y height、十字鍵控制 Motor6、七路 relay 或 `arm_gripper_*`，都只作歷史記錄。

啟動：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./r1_start_base_1_0.sh
```

固定控制：

```text
左搖桿：底盤按 D-pad 選定的人視角平移
右搖桿：底盤旋轉，max_rotation=3.0 rad/s
D-pad：設定 KFS gripper / visual front 在機手視角中的方向
SELECT/中左：STAFF mode
START/中右：KFS mode
X+Y+B+A 長按 5 秒：Raspberry Pi shutdown command
```

STAFF mode：

```text
A -> Motor7 90° / preset cycle
X -> Motor8 90° / preset cycle
B -> Motor7 staff gripper relay toggle
Y -> Motor8 staff gripper relay toggle
R1/R2 -> Motor7 trim -/+
L1/L2 -> Motor8 trim -/+
R3/P1 -> Motor7 inclination/head relay
L3/P2 -> Motor8 inclination/head relay
```

STAFF mode 且 D-pad 下：

```text
A -> Motor8 preset，X -> Motor7 preset
B -> Motor8 relay，Y -> Motor7 relay
R1 -> Motor8 trim positive，R2 -> Motor8 trim negative
L1 -> Motor7 trim positive，L2 -> Motor7 trim negative
R3/P1 -> Motor8 inclination，L3/P2 -> Motor7 inclination
```

KFS mode：

```text
Y -> KFS gripper toggle
L1/R1 -> Motor5 elevator negative/down、positive/up
L2/R2 -> Motor6 horizontal positive/out、negative/in
```

Arduino 五路 relay：

```text
[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
full safe_state = [0,1,0,1,0]
```


## 日常啓動

```bash
ssh robotics@你的機器人IP
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
./r1_start_base_1_0.sh
```

腳本會進入 tmux。離開但保持運行：

```text
Ctrl+b，然後按 d
```

重新進入：

```bash
tmux attach -t r1_control
```

停止全部：

```bash
tmux kill-session -t r1_control
```

## 手柄要求

- 8BitDo 手柄使用 X 模式。
- 當前 `Joystick.msg` 數值範圍為 `-512 .. 512`。
- L2/R2 trigger 範圍為 `0 .. 512`。
- 當前死區為 `15`（約滿量程 2.93%）。

檢查手柄：

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

KFS mode：
Y: KFS gripper toggle
L1/R1: Motor5 elevator negative/down、positive/up
L2/R2: Motor6 horizontal positive/out、negative/in
```

D-pad 下的 STAFF swap 詳細規則看本文最上方 source-verified 區塊或 `CONTROLLER_USAGE.md`。

## 底盤速度曲線

當前默認配置：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
translation curve = 0.1x + 0.9x^3
max_rotation = 3.0
rotation_linear_weight = 0.1
rotation curve = 0.1x + 0.9x^3
```

查看：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge translation_linear_weight
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge rotation_linear_weight
ros2 param get /local_navigation_node max_wheel_speed_rad_s
ros2 param get /local_navigation_node max_wheel_accel_rad_s2
ros2 param get /local_navigation_node accel_limit_mode
```

START/SELECT 當前不用於底盤調速，只切換 STAFF/KFS mode。左搖桿平移與右搖桿旋轉都使用 `0.1x + 0.9x³`；滿桿分別達到 `150 cm/s` 和 `3.0 rad/s`。Motor7/8 staff gripper 目前使用 POS_VEL position controller，不再使用舊 R2/L2 速度型 arm_gripper 曲線。

## 安全保護

當前鏈路有多層 timeout：

```text
joystick_bridge:
  /joystick_data 超過 0.3s 未更新
  -> /local_driving = [0,0,0]

local_navigation_node:
  /local_driving 超過 0.3s 未更新
  -> Motor 1-4 發送 0 rad/s

damiao_node:
  連續 VEL 命令超過 0.5s 未刷新
  -> 對應 motor_id 發送 0 rad/s

r1_arm_control:
  執行機構 speed_cmd 超過 0.3s 未刷新
  -> 對應 Motor 5/6/7 發送 0 rad/s

arduino_pneumatic_driver:
  /pneumatic_gripper_cmd 超過 0.5s 未刷新
  -> safe_state = [0,1] = LOW + CLOSE
```

## 常用檢查

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

## 如果沒有反應

按順序檢查：

1. `tmux attach -t r1_control` 查看對應窗口是否退出。
2. `ros2 node list` 確認節點存在。
3. `ros2 topic echo /joystick_data` 確認手柄數據變化。
4. `ros2 topic echo /local_driving` 確認底盤指令變化。
5. 查看 `motors` 窗口確認達妙驅動已連接。
6. 確認 `/dev/ttyACM0` 是達妙 USB-CAN，Arduino relay 在 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`。

## ROS2 domain isolation

`r1_start_base_1_0.sh` now isolates R1 from R2 by exporting:

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

Use SSH into R1 to run `ros2 node list` / `ros2 topic echo`. Do not remove this isolation unless remote ROS2 debugging from another computer is required.

## 2026-06-07 急停後自動恢復

`damiao_node` 現在會在反饋超時或電機反饋失能後自動執行 `VEL mode + enable + 0 rad/s`。恢復時不需要重啓 bash，但必須先把搖桿和控制按鈕全部松開回中，等 `/damiao_motor_status` 的 `state_code` 從 `0` 經過 `1` 變為 `2`，才允許再次運動。

```bash
ros2 topic echo /damiao_motor_status
```


## 2026-06-12 Motor 8 位置實驗操作

```text
X: Motor 8 在位置 A/B 間切換
L3: Motor 8 負向微調
R3: Motor 8 正向微調
```

默認試驗值為 A=`0.0 rad`、B=`0.3 rad`、軟限位=`-0.5..0.5 rad`。第一次測試必須
離地或解除機構負載。啓動後先確認：

```bash
ros2 topic echo /damiao_motor_status
ros2 topic echo /motor8_position_status
```

Motor 8 的 `/damiao_motor_status` 應顯示 `motor_id=8`、`feedback_fresh=1`、
`enabled=1`、`active_control_mode=2`。沒有看到這些狀態時不要按 X。

## 2026-06-13 Motor 7/8 位置控制按鍵

```text
啓動默認：Motor 7
START (+)：Motor 7 / Motor 8 切換
X：當前電機 A/B 切換
L2：當前電機負向微調
R2：當前電機正向微調
```

切換時必須先松開 X、L2、R2。查看當前選擇：

```bash
ros2 topic echo /motor_position_selector_status
```

其中 `data[0]` 為當前電機 ID，正常啓動應為 `7.0`。

## 2026-06-13 Motor 7/8 三位置操作

當前所選電機每短按一次 X：

```text
第一次：0 -> +32 rad
第二次：+32 -> -32 rad
第三次：-32 -> 0 rad
```

`/motor7_position_status` 或 `/motor8_position_status` 的 `data[3]` 表示當前預設：

```text
0 = 0 rad
1 = +32 rad
2 = -32 rad
```


## 2026-06-13 雙 arm 氣動按鈕

啓動默認選擇 Motor7。Motor7/8 的電機位置與氣動功能共用同一個選擇狀態：

```text
START/+ : Motor7 / Motor8 切換
X       : 所選電機循環 0 / +32 / -32 rad
L2/R2   : 所選電機負向/正向微調
A       : 所選 arm height 高低切換
B       : 所選 arm gripper 開關切換
SELECT/-: 只在選中 Motor8 時切換 inclination 高低
Y       : KFS gripper 開關切換，與 Motor7/8 選擇無關
```

按 START 只切換控制對象，不改變任何已鎖定氣動狀態。不要同時按 START 和其他機構按鈕。


## 2026-06-14 歷史手柄配置記錄（已被 STAFF/KFS mode 取代）

本段原本記錄 START 選 Motor7/8、A/B 控所選 arm pneumatic、十字鍵控制 Motor6 的方案。該方案已被目前 STAFF/KFS mode、五路 relay、D-pad KFS visual-front 視角方案取代，不再作為實機操作依據。

目前操作請看本文最上方 `2026-06-20 Source-Verified Current How To Use` 或根目錄 `CONTROLLER_USAGE.md`。

## 2026-06-16 8BitDo P1／P2 背鍵配置

P1／P2 目前不作為獨立 ROS 按鍵使用。`evtest` 實測 A/B/X/Y 有事件，但 P1／P2
沒有獨立事件，因此不修改 `Joystick.msg` 或 `joystick_node.py`。

目前在 8BitDo 軟體中使用手柄內部 remap：

```text
P1 = R3
P2 = L3
```

所以實際操作為：

```text
按下 P1：等同 R3，只在 STAFF mode 切換 Motor7 inclination/head relay
按下 P2：等同 L3，只在 STAFF mode 切換 Motor8 inclination/head relay
KFS mode 不使用 P1/P2；Motor6 horizontal 目前由 L2/R2 控制
```

這只是手柄硬體層的按鍵替代，不新增 ROS topic、message 欄位或 node。原本 L3／R3
仍保留同樣功能。

## 2026-06-18 七路 Arduino 氣動 panel（歷史過渡記錄，已由下一節取代）

當時新 Arduino sketch 使用 7 路 relay，pin 為 `22..28`。ROS 操作按鍵不變，只有底層
Arduino serial command 從 6 路變為 7 路。

目前完整 relay 順序：

```text
[relay1, relay2, relay3, relay4, relay5, relay6, relay7]
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, reserved]
```

完整 safe state：

```text
[0,0,1,0,1,1,0]
```

Relay 7 / Pin 28 暫時 reserved，保持 `0/OFF`，不由任何手柄按鍵控制。A/B/SELECT/Y/START 的
現有操作不變。

## 2026-06-18 Relay 7 = Motor7 inclination

Relay 7 / Pin 28 現在不是 reserved，而是 Motor7 inclination。完整 relay 順序：

```text
[KFS, M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

目前 SELECT/- 行為：

```text
START 選中 Motor7：SELECT 切換 Motor7 inclination
START 選中 Motor8：SELECT 切換 Motor8 inclination
```

A/B 仍控制目前選中 arm 的 height/gripper；Y 仍控制 KFS；Arduino 完整 safe state 仍為：

```text
[0,0,1,0,1,1,0]
```


## 2026-06-18 Controller-gated autostart

本版本新增開機自動啟動 watcher，但不是開機立即啟動整套 ROS。流程是：

```text
Raspberry Pi 開機
-> systemd 啟動 scripts/wait_and_start_robot.sh
-> watcher 每 1 秒掃描 active controller input device
-> 偵測到 8BitDo / Xbox controller active
-> 自動執行 r1_start_base_1_0.sh
-> 建立 tmux session r1_control
```

預設安全策略：

```text
STOP_ON_CONTROLLER_LOST=0
```

也就是手柄中途關掉或短暫斷線時，不會自動 kill 整套 ROS。底盤、氣動、Motor7/8 等控制鏈路仍依靠各自 node 的 timeout / watchdog 進入安全輸出。這樣比賽現場不會因短暫手柄斷線而把整個 tmux session 關掉。

如果之後確定要「手柄關掉就停止整套系統」，可以在 service 中改：

```text
Environment=STOP_ON_CONTROLLER_LOST=1
```

但正式比賽建議先保持 `0`。

### 手動測試 watcher 語法

先不要安裝 systemd service，可以手動跑：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./scripts/wait_and_start_robot.sh
```

預期：

```text
手柄未開：反覆顯示 waiting for controller...
手柄打開：顯示 controller active; starting robot system
之後建立 tmux session r1_control
```

查看 tmux：

```bash
tmux attach -t r1_control
```

停止整套 ROS：

```bash
tmux kill-session -t r1_control
```

停止 watcher：在 watcher terminal 按 `Ctrl-C`。

### 安裝 systemd autostart

確認手動測試成功後再安裝：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
sudo cp systemd/r1-control-autostart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable r1-control-autostart.service
sudo systemctl start r1-control-autostart.service
```

查看狀態與 log：

```bash
systemctl status r1-control-autostart.service
journalctl -u r1-control-autostart.service -f
```

停用 autostart：

```bash
sudo systemctl disable --now r1-control-autostart.service
```

### 相關文件

```text
scripts/wait_and_start_robot.sh
systemd/r1-control-autostart.service
r1_start_base_1_0.sh
```

`r1_start_base_1_0.sh` 新增 `R1_NO_TMUX_ATTACH=1` 支援。systemd watcher 使用這個環境變數建立 tmux session，但不嘗試 attach，避免 background service 卡住或因沒有 terminal 而失敗。

## 2026-06-18 手柄四鍵長按關機 dry-run

新增 `robot_power_control` package 與 `joystick_shutdown_node`。目前 `r1_start_base_1_0.sh` 會啟動一個 `power_shutdown` tmux window，但預設使用安全測試模式：

```text
dry_run = true
```

目前按鍵組合：

```text
X + Y + B + A 同時長按 5 秒
```

dry-run 模式下不會真的關機，只會發布：

```text
/robot_power_status = DRY_RUN shutdown_combo_held
```

監控：

```bash
ros2 topic echo /robot_power_status
```

真正啟用關機前，必須先設定 sudoers 精確授權：

```text
robotics ALL=NOPASSWD: /usr/bin/systemctl poweroff
```

然後才可以把啟動參數改為：

```text
dry_run:=false
```

目前已完成 dry-run 實機確認並已把啟動腳本切到 `dry_run:=false`。四鍵長按會直接呼叫 `sudo -n /usr/bin/systemctl poweroff`。不要再讓 node 先 kill tmux，否則會把自己殺掉而無法執行 poweroff。


## 2026-06-19 KFS gripper 人視角底盤控制（取代 2026-06-14 E-stop 基準）

本節是視角方案演進記錄；目前操作以本文最上方 source-verified 區塊和 `CONTROLLER_USAGE.md` 為準。當時說明：十字鍵表示 **KFS gripper 在你眼中的方向**，不是 E-stop／車頭方向。

```text
十字鍵上：KFS gripper 在你的前方，view=0
十字鍵右：KFS gripper 在你的右方，view=1
十字鍵下：KFS gripper 在你的後方／靠近你，view=2
十字鍵左：KFS gripper 在你的左方，view=3
```

開機預設 `view=2`，因為目前比賽站位假設 KFS gripper 先朝向操作人。左搖桿必須回中才接受新的十字鍵方向；十字鍵不會令底盤旋轉，只更新左搖桿的人視角換算。

目前實物幾何：E-stop 在北方時，KFS gripper 在西方。所以程式內部會用：

```text
E-stop/body-front view = (KFS view + 1) % 4
```

例子：你看到 KFS gripper 在左邊，先鬆開左搖桿，按十字鍵左；之後左搖桿向前，機器應該在你眼中向前平移。

查看目前 KFS 視角：

```bash
ros2 topic echo /view_orientation
```


## 2026-06-19 KFS gripper 車頭標控制（取代同日 KFS +1 偏移方案）

本節是視角方案演進記錄；目前操作以本文最上方 source-verified 區塊和 `CONTROLLER_USAGE.md` 為準。當時說明：KFS gripper 是機器上最大、最顯眼的方向標記，因此把 **KFS gripper 當作車頭／機器前方**。

```text
十字鍵上：KFS gripper／車頭 在你的前方，view=0
十字鍵右：KFS gripper／車頭 在你的右方，view=1
十字鍵下：KFS gripper／車頭 在你的後方／靠近你，view=2
十字鍵左：KFS gripper／車頭 在你的左方，view=3
```

開機預設 `view=2`，因為目前假設 KFS gripper 先朝向操作人。程式內部現在使用：

```text
body_front_view = KFS view
```

也就是不再使用舊版 `E-stop view = (KFS view + 1) % 4`。左搖桿必須回中才接受新的十字鍵方向；十字鍵不會命令底盤旋轉。


## 2026-06-19 KFS gripper 開機預設在前方

本節取代同日 v2.2 中「開機預設 view=2」的說明。現在開機預設等同 **D-pad 上**：

```text
開機預設：view=0
意思：KFS gripper／車頭 在你的前方
```

KFS gripper 仍直接作為車頭標，十字鍵語義不變。若實際車身方向改變，仍需要左搖桿回中後按對應十字鍵重新同步。


## 2026-06-19 KFS 車頭標 90 度校正

本節取代 v2.3 的換算公式。實機測到：KFS gripper 在最前方時，按十字鍵左再推左搖桿向上，機器才在你眼中向前；按十字鍵上則向左走。這代表底盤內部 body frame 與 KFS 視覺車頭差 90 度。

現在已校正為：

```text
body_front_view = (KFS view - 1) % 4
```

操作語義不變：

```text
十字鍵上：KFS gripper／視覺車頭 在你的前方
十字鍵右：KFS gripper／視覺車頭 在你的右方
十字鍵下：KFS gripper／視覺車頭 在你的後方
十字鍵左：KFS gripper／視覺車頭 在你的左方
```

開機仍預設 `view=0`，也就是 KFS 在前。校正後，KFS 在前時不按十字鍵或按十字鍵上，左搖桿向前應該在你眼中向前走。


## 2026-06-19 STAFF/KFS mode 過渡鍵位記錄（已被現行總表取代）

本段原本包含多次同日鍵位迭代，例如 A/Y height、Y/A 同時控制 preset 和 relay、以及五路 relay 的中間版本。這些內容已被後面的 `2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）` 和本文最上方 `2026-06-20 Source-Verified Current How To Use` 取代。

目前實機只採用：STAFF mode `A/X` 控 Motor7/8 preset，`B/Y` 控 Motor7/8 staff gripper relay，`R3/L3` 控 Motor7/8 inclination；KFS mode `Y` 控 KFS gripper，`L1/R1` 控 Motor5，`L2/R2` 控 Motor6。

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
