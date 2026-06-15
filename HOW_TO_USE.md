# R1 使用說明

本說明面向日常操作。當前完整系統以 `r1_start_base_1_0.sh` 為入口；`start.sh`、`start_background.sh` 只保留為舊底盤 4 節點流程，不建議作為 R1 完整系統首選。

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
左搖桿上/下: 底盤前進/後退
左搖桿左/右: 底盤左/右橫移
右搖桿左/右: 底盤原地旋轉
R1: Motor 5 elevator 正向，固定速度
L1: Motor 5 elevator 反向，固定速度
D-pad 左/右: Motor 6 horizontal 左/右移動
D-pad 上/下: Motor 6 horizontal power level 增加/減少
START/SELECT: 當前不用於底盤調速
R2: Motor 7 arm gripper 正向，按壓深度調速
L2: Motor 7 arm gripper 反向，按壓深度調速
B: arm pneumatic gripper OPEN while held，松開 CLOSE
A: arm pneumatic height LOW latch
X: arm pneumatic height HIGH latch
Y: KFS staff gripper OPEN，松開 CLOSE
R3: 當前不使用
```

## 底盤速度曲線

當前默認配置：

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

START/SELECT 當前不用於底盤調速。左搖桿平移與右搖桿旋轉都使用 `0.1x + 0.9x³`；滿桿分別達到 `150 cm/s` 和 `1.2 rad/s`。Motor 7 的 R2/L2 也使用同一曲線，滿按達到 `1.3 rad/s`。

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
第一次：0 -> +35 rad
第二次：+35 -> -35 rad
第三次：-35 -> 0 rad
```

`/motor7_position_status` 或 `/motor8_position_status` 的 `data[3]` 表示當前預設：

```text
0 = 0 rad
1 = +35 rad
2 = -35 rad
```


## 2026-06-13 雙 arm 氣動按鈕

啓動默認選擇 Motor7。Motor7/8 的電機位置與氣動功能共用同一個選擇狀態：

```text
START/+ : Motor7 / Motor8 切換
X       : 所選電機循環 0 / +35 / -35 rad
L2/R2   : 所選電機負向/正向微調
A       : 所選 arm height 高低切換
B       : 所選 arm gripper 開關切換
SELECT/-: 只在選中 Motor8 時切換 inclination 高低
Y       : KFS gripper 開關切換，與 Motor7/8 選擇無關
```

按 START 只切換控制對象，不改變任何已鎖定氣動狀態。不要同時按 START 和其他機構按鈕。


## 2026-06-14 目前完整手柄按鍵配置（現行唯一操作依據）

本節取代前面歷史章節中的舊按鍵說明。前面的 Motor7 速度模式、Motor8 `L3/R3` 微調、
氣動夾爪按住控制等內容只保留作版本回溯，不再代表目前正式啟動配置。

### 全部按鍵

| 手柄輸入 | 目前功能 | 操作方式 |
|---|---|---|
| 左搖桿上／下 | 底盤前進／後退 | 持續推動 |
| 左搖桿左／右 | 底盤左／右橫移 | 持續推動 |
| 左搖桿斜向 | 底盤斜向平移 | 持續推動 |
| 右搖桿左／右 | 底盤原地旋轉 | 持續推動 |
| 右搖桿上／下 | 未使用 | - |
| 十字鍵左 | Motor6 horizontal 負方向 | 按住移動，放開停止 |
| 十字鍵右 | Motor6 horizontal 正方向 | 按住移動，放開停止 |
| 十字鍵上 | 提高 Motor6 horizontal 速度檔 | 每按一次提高一檔 |
| 十字鍵下 | 降低 Motor6 horizontal 速度檔 | 每按一次降低一檔 |
| `L1` | Motor5 elevator 負方向 | 按住移動，放開停止 |
| `R1` | Motor5 elevator 正方向 | 按住移動，放開停止 |
| `L2` | 目前所選 Motor7/8 負方向微調 | 按壓深度控制微調量 |
| `R2` | 目前所選 Motor7/8 正方向微調 | 按壓深度控制微調量 |
| `A` | 目前所選 arm height 高／低切換 | 每按一次切換並保持 |
| `B` | 目前所選 arm gripper 開／關切換 | 每按一次切換並保持 |
| `X` | 目前所選 Motor7/8 三個預設位置循環 | 每按一次切換位置 |
| `Y` | KFS gripper 開／關切換 | 每按一次切換並保持 |
| `START/+` | 選擇 Motor7 或 Motor8 | 每按一次切換控制對象 |
| `SELECT/-` | Motor8 inclination 高／低切換 | 只有選中 Motor8 時有效 |
| `L3` | 未使用 | - |
| `R3` | 未使用 | - |

### Motor7／Motor8 選擇邏輯

系統啟動時預設選中 `Motor7`：

```text
按一次 START/+：Motor7 -> Motor8
再按一次 START/+：Motor8 -> Motor7
```

`START/+` 只改變目前控制對象，不會立即改變任何電機位置或氣動鎖定狀態。切換前必須先
放開 `X`、`L2`、`R2`；其中任何一個仍在操作時，本次切換會被阻止。

選中 Motor7 時：

```text
X       : Motor7 三位置循環
L2/R2   : Motor7 位置微調
A       : Motor7 arm height
B       : Motor7 arm gripper
SELECT/-: 無動作
```

選中 Motor8 時：

```text
X       : Motor8 三位置循環
L2/R2   : Motor8 位置微調
A       : Motor8 arm height
B       : Motor8 arm gripper
SELECT/-: Motor8 inclination
```

Motor7 與 Motor8 分別保存自己的位置目標和氣動狀態。`Y` 控制 KFS，完全不受 Motor7／8
選擇影響。

### Motor7／Motor8 三個預設位置

每次短按 `X` 的循環順序：

```text
第一次：目前位置 -> +35 rad
第二次：+35 rad -> -35 rad
第三次：-35 rad -> 0 rad
之後重複循環
```

`L2/R2` 用於在軟限位 `-35..+35 rad` 內微調目標位置，預設最大微調速度為 `2 rad/s`。

### Motor6 horizontal 速度檔

Motor6 啟動預設為 20% 檔。十字鍵上／下只切換速度檔，不會直接令 Motor6 移動：

```text
20% = 4 rad/s
50% = 10 rad/s
100% = 20 rad/s
```

切換速度檔後，使用十字鍵左／右控制實際移動方向。

### 同時按鍵行為

```text
L1 + R1                : Motor5 停止
深度相同的 L2 + R2     : Motor7/8 微調互相抵消
X、L2 或 R2 操作期間按 +: 不切換 Motor7/8
Motor7 模式按 SELECT/- : 無動作
```

### 目前底盤上限

```text
最大平移速度：150 cm/s
最大旋轉速度：1.2 rad/s
```

目前左搖桿使用底盤自身座標：底盤旋轉後，搖桿向前仍代表「底盤目前正前方」，不是固定的
場地方向。現階段尚未加入 IMU 或手動 90 度方向偏移功能。


## 2026-06-14 人視角底盤測試配置（取代上一版十字鍵功能）

本節是目前最新操作依據。十字鍵不再控制 Motor6，而是告訴程式 E-stop／車頭在人視角中的
方向；按十字鍵不會令底盤旋轉。

```text
十字鍵上：E-stop 在人的前方
十字鍵右：E-stop 在人的右方
十字鍵下：E-stop 在人的後方
十字鍵左：E-stop 在人的左方
```

左搖桿必須先回中才接受新的方向。視角設定後，左搖桿永遠按人的前後左右解讀；右搖桿
仍直接控制底盤旋轉。

例如底盤向左轉 90 度、E-stop 在人視角左邊：

```text
1. 鬆開左搖桿
2. 按十字鍵左
3. 左搖桿向前
4. 底盤以車體向右橫移，實際向人的前方移動
```

Motor6 新按鍵：

```text
L3：Motor6 負方向
R3：Motor6 正方向
L3 + R3：停止
固定命令速度：10 rad/s
```

查看目前視角：

```bash
ros2 topic echo /view_orientation
```

```text
0 = E-stop 在人前方
1 = E-stop 在人右方
2 = E-stop 在人後方
3 = E-stop 在人左方
```

其他按鍵保持不變：`L1/R1` 控制 Motor5，`START/X/L2/R2` 控制 Motor7／8，`A/B` 控制
所選 arm 氣動，`SELECT/-` 控制 Motor8 inclination，`Y` 控制 KFS。

實機結果（2026-06-15）：四個人視角方向及 Motor6 `L3/R3` 控制均測試成功，正式保留此配置。
