> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# r1_arm_control

R1 机械臂控制 package。当前用于控制速度型达妙电机执行机构：升降、水平移动、夹爪。

## 更新记录

### 2026-06-07 v4 Motor 7 混合三次曲线

- Motor 7 的 R2/L2 净输入改为 `y = 0.1x + 0.9x³`。
- 新增 `gripper_linear_weight = 0.1`，允许在 `0.0..1.0` 范围动态调整。
- `max_speed_rad_s = 1.3`、`trigger_deadzone = 24`、topic 和 controller watchdog 均保持不变。
- R2/L2 同时按下时先计算净输入；相同深度仍输出 `0 rad/s`。

### 2026-06-07 v3 升降与机械夹爪按键交换

- Motor 5 升降改为 `R1/L1` 数字按钮固定速度控制。
- `R1` 为升降正向，`L1` 为升降反向，同时按下或同时松开时停止。
- Motor 7 机械夹爪改为 `R2/L2` 模拟扳机控制。
- `R2` 为夹爪正向，`L2` 为夹爪反向，按压深度决定速度。
- Motor 7 旧的 0.5 s 两段速度与 START/SELECT 调速逻辑已移除。
- Motor ID、command topic 和 controller timeout 均不变。

### 2026-05-14 v1 安全版本

- 新增并确认三个执行机构 controller：
  - `elevator_controller_node`
  - `horizontal_controller_node`
  - `arm_gripper_controller_node`
- 新增三个 joystick bridge：
  - `elevator_joystick_bridge_node`
  - `horizontal_joystick_bridge_node`
  - `arm_gripper_joystick_bridge_node`
- 所有 controller 均包含 `timeout_sec` 失效保护。
- 夹爪默认速度降为 `1.0 rad/s`，避免动作过快。

### 2026-06-07 v2 Motor 7 两段式速度（历史记录，已被 v3 覆盖）

- `R1/L1` 按住前 `0.5 s` 使用 `0.3 rad/s`。
- 持续按住超过 `0.5 s` 后切换到高速档，默认 `1.3 rad/s`。
- `START (+)` / `SELECT (-)` 以 `0.1 rad/s` 调整高速档。
- 高速档限制在 `0.3 ~ 1.3 rad/s`。

## 适用范围

本 package 适用于 R1 当前机械臂的速度控制执行机构。node 绑定的是“升降 / 水平 / 夹爪”这类机构职责，不绑定某一年比赛流程或战术状态机。

## Nodes

### elevator_controller_node

订阅：

```text
/elevator_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control std_msgs/msg/Float32MultiArray
data = [motor_id, 3.0, speed_rad_s, 0.0]

/elevator_status std_msgs/msg/Float32MultiArray
data = [target_speed, commanded_speed, timeout_active, motor_id]
```

参数：

```text
motor_id = 5
max_speed_rad_s = 28.0
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

### horizontal_controller_node

订阅：

```text
/horizontal_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control
/horizontal_status
```

参数：

```text
motor_id = 6
max_speed_rad_s = 30.0
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

### arm_gripper_controller_node

订阅：

```text
/arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray
data[0] = target speed, rad/s
```

发布：

```text
/damiao_control
/arm_gripper_status
```

参数：

```text
motor_id = 7
max_speed_rad_s = 1.3
timeout_sec = 0.3
publish_hz = 20.0
max_accel_rad_s2 = 0.0
```

## Joystick Bridge Nodes

### elevator_joystick_bridge_node

```text
R1: 升降正向，固定速度
L1: 升降反向，固定速度
R1 + L1: 停止
发布: /elevator_speed_cmd
```

参数：

```text
command_speed_rad_s = 28.0
```

### horizontal_joystick_bridge_node

```text
KFS mode L2: Motor6 horizontal positive/out
KFS mode R2: Motor6 horizontal negative/in
发布: /horizontal_speed_cmd
```

参数：

```text
command_speed_rad_s = 30.0
trigger_deadzone = 24
```

### arm_gripper_joystick_bridge_node

```text
R2: 夹爪正向，按压越深速度越高
L2: 夹爪反向，按压越深速度越高
R2 + L2: 先计算两者净输入；相同深度时停止
曲线: y = 0.1x + 0.9x³
发布: /arm_gripper_speed_cmd
```

参数：

```text
max_speed_rad_s = 1.3
trigger_deadzone = 24
gripper_linear_weight = 0.1
trigger range = 0..512
```

理论目标速度（只按一个扳机）：

| 扳机深度 | Motor 7 速度绝对值 |
|---:|---:|
| 10% | 0.014 rad/s |
| 25% | 0.051 rad/s |
| 50% | 0.211 rad/s |
| 75% | 0.591 rad/s |
| 100% | 1.300 rad/s |

## 超时保护

三个 controller 都实现相同的 timeout 逻辑。

触发条件：

```text
超过 timeout_sec 没有收到对应的 speed_cmd topic
```

默认值：

```text
timeout_sec = 0.3 s
```

超时行为：

```text
target_speed = 0.0
继续向 /damiao_control 发布 0 rad/s
status topic 中 timeout_active = 1.0
```

调整示例：

```bash
ros2 param set /elevator_controller_node timeout_sec 0.3
ros2 param set /horizontal_controller_node timeout_sec 0.3
ros2 param set /arm_gripper_controller_node timeout_sec 0.3
```

## 最小启动示例

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
source install/setup.bash
ros2 run r1_arm_control arm_gripper_controller_node
```

另一个 terminal 发布测试命令：

```bash
source install/setup.bash
ros2 topic pub /arm_gripper_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.5]}" --once
```

如果只发布一次，`timeout_sec` 后会自动归零。

## 调试方式

```bash
ros2 topic echo /elevator_status
ros2 topic echo /horizontal_status
ros2 topic echo /arm_gripper_status
ros2 topic echo /damiao_control
```


## 2026-06-12 v5 Motor 8 双位置 POS_VEL 实验

本版本不修改 Motor 7。新增 Motor 8 作为 DM-S3519 位置速度模式实验电机，复用唯一的
`damiao_node` 和现有 `/damiao_control` 底层接口。

### Nodes

#### motor8_position_joystick_bridge_node

订阅：

```text
/joystick_data my_joystick_msgs/msg/Joystick
```

发布：

```text
/motor8_position_input std_msgs/msg/Float32MultiArray
数据: [toggle_event, trim_input, input_valid]
```

默认控制：

```text
X: 在位置 A/B 之间切换，上升沿只触发一次
L3: 目标角度负向微调
R3: 目标角度正向微调
L3 + R3: 相互抵消
```

参数：

```text
toggle_button = "x"
negative_trim_button = "l3"
positive_trim_button = "r3"
publish_hz = 20.0 Hz
input_timeout_sec = 0.3 s
```

超过 `input_timeout_sec` 未收到 `/joystick_data` 后发布
`[0.0, 0.0, 0.0]`，禁止切换并停止微调。

#### motor8_position_controller_node

订阅：

```text
/motor8_position_input
/damiao_motor_status
```

发布：

```text
/damiao_control = [8.0, 2.0, max_speed_rad_s, target_position_rad]
/motor8_position_status = [target_q, actual_q, actual_dq, selected_position,
                           trim_input, feedback_valid, input_timeout,
                           motor_id, at_target]
```

默认参数仅用于低速离地实验：

```text
motor_id = 8
position_a_rad = 0.0 rad
position_b_rad = 0.3 rad
min_position_rad = -0.5 rad
max_position_rad = 0.5 rad
preset_speed_rad_s = 0.3 rad/s
trim_speed_rad_s = 0.1 rad/s
hold_speed_rad_s = 0.1 rad/s
position_tolerance_rad = 0.03 rad
input_timeout_sec = 0.3 s
feedback_timeout_sec = 0.5 s
publish_hz = 20.0 Hz
```

controller 只有在 Motor 8 反馈新鲜、已使能且驱动器报告 `POS_VEL` 时才发布运动命令。
启动、急停恢复或反馈重新出现时，先将目标同步为实时位置，不重放恢复前的旧预设。
手柄断连或 bridge topic 超时后，目标收回到实时位置并保持。所有预设和微调都经过
`min_position_rad` / `max_position_rad` 软限位。

### 启动

```bash
ros2 run r1_arm_control motor8_position_controller_node
ros2 run r1_arm_control motor8_position_joystick_bridge_node
```

完整系统执行 `./r1_start_base_1_0.sh` 时会自动启动这两个节点。

### 调试

```bash
ros2 topic echo /motor8_position_input
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
ros2 topic echo /damiao_control

ros2 param get /motor8_position_controller_node position_a_rad
ros2 param get /motor8_position_controller_node position_b_rad
ros2 param set /motor8_position_controller_node position_b_rad 0.2
```

首次实机测试必须让机构脱离负载或确保不会撞限位，并保持急停可立即操作。DM-S3519
上电位置会被当前 `damiao_node` 置为 `0 rad`，所以 A/B 是相对于本次启动位置的角度，
不是断电保持的机械绝对位置。

## 2026-06-13 v6 Motor 8 实机初测默认参数

Motor 8 在无危险机械负载的初步测试中，以下运行参数能够完成多圈位置控制，现固化为
`motor8_position_controller_node` 的源码默认值：

```text
position_a_rad = 0.0 rad
position_b_rad = 33.0 rad
min_position_rad = -32.0 rad
max_position_rad = 32.0 rad
preset_speed_rad_s = 3.0 rad/s
trim_speed_rad_s = 2.0 rad/s
```

换算后，位置 B 约为 `5.25` 圈，软限位单方向约为 `5.57` 圈。X 仍在 A/B 间切换，
L3/R3 仍在软限位内微调。该结果属于初测值，后续装入真实机构后仍需根据机械限位、
负载和方向继续调整。

注意：当前 DM-S3519 反馈解码参数仍使用 `PMAX = 12.5 rad`。虽然实机初测确认
`33 rad` 目标能够驱动电机多圈旋转，但超过 `+-12.5 rad` 后，必须继续观察
`actual_q` 是否饱和，以及到位判断、手柄断连保持和急停恢复后的当前位置同步是否可靠。
在这些保护行为完成实测前，不应直接把同样参数用于有碰撞风险的机构。

## 2026-06-13 v7 Motor 7/8 共享位置控制

主启动路径现将 Motor 7 和 Motor 8 都设为 `POS_VEL`。两个电机复用同一个位置 controller
实现，但使用独立节点、独立 input/status topic 和独立参数状态。

默认按键：

```text
启动默认选择 Motor 7
START (+): 在 Motor 7 / Motor 8 之间切换
X: 当前所选电机在 A/B 两个位置间切换
L2: 当前所选电机负向微调，按压深度决定微调速度
R2: 当前所选电机正向微调，按压深度决定微调速度
```

只有当 X、L2、R2 全部松开时，START 才允许切换。未选中的电机持续收到有效的零微调
输入，保持自己的目标位置，不会接收另一台电机的 A/B 目标。

节点与接口：

```text
/motor_position_selector_joystick_bridge_node
  -> /motor7_position_input [toggle, trim, valid]
  -> /motor8_position_input [toggle, trim, valid]
  -> /motor_position_selector_status [selected_motor_id, input_valid, switch_blocked]

/motor7_position_controller_node
  -> /motor7_position_status
  -> /damiao_control [7, 2, speed, target_position]

/motor8_position_controller_node
  -> /motor8_position_status
  -> /damiao_control [8, 2, speed, target_position]
```

Motor 7 與 Motor 8 當時實驗參數曾短暫設為以下值；目前 source-verified 預設請看下一節 v8：

```text
position_a_rad = 0.0 rad
position_b_rad = 33.0 rad
min_position_rad = -35.0 rad
max_position_rad = 35.0 rad
preset_speed_rad_s = 3.0 rad/s
trim_speed_rad_s = 2.0 rad/s
```

旧 `arm_gripper_controller_node` 和 `arm_gripper_joystick_bridge_node` 文件仍保留用于历史回溯，
但 `r1_start_base_1_0.sh` 不再启动它们，避免 Motor 7 的 VEL 与 POS_VEL 命令冲突。

## 2026-06-13 v8 Motor 7/8 三位置循环

Motor 7 和 Motor 8 的 preset 由兩點改為三點，两个 controller 使用相同源码默认值。現行 bridge 映射為 `A -> Motor7`、`X -> Motor8`：

```text
position_a_rad = 0.0 rad       # selected_position = 0
position_b_rad = 32.0 rad      # selected_position = 1
position_c_rad = -32.0 rad     # selected_position = 2
min_position_rad = -32.0 rad
max_position_rad = 32.0 rad
```

每次短按對應 preset 鍵的循環順序：

```text
0 rad -> +32 rad -> -32 rad -> 0 rad
```

Motor 7 和 Motor 8 分别保存自己的 `selected_position`。Motor7 和 Motor8 各自保存自己的 `selected_position`。目前不再使用 START 選電機；STAFF mode 下 `A` 直接切 Motor7，`X` 直接切 Motor8。R1/R2 控 Motor7 微調，L1/L2 控 Motor8 微調，範圍為 `-32..32 rad`。


## 2026-06-14 v9 Motor6 改用 L3／R3

本節取代 Motor6 使用十字鍵和三段 power level 的目前行為說明；舊內容保留作版本回溯。
十字鍵已讓給底盤人視角選擇，Motor6 horizontal 改為：

```text
L3：Motor6 正方向，按住移動
R3：Motor6 負方向，按住移動
L3 + R3：停止
全部鬆開：停止
```

`horizontal_joystick_bridge_node` 新參數：

| 參數 | 預設值 | 單位 | 作用 |
|---|---:|---|---|
| `command_speed_rad_s` | `10.0` | rad/s | L3／R3 固定命令速度 |

發布 topic 仍為 `/horizontal_speed_cmd`，下游 `horizontal_controller_node`、Motor6 VEL 模式、
`max_speed_rad_s=20.0` 和 `timeout_sec=0.3 s` 均未改變。若 bridge 或 joystick topic 停止，
下游超時後會輸出 Motor6 `0 rad/s`。

## 2026-06-16 v10 Motor6 P1／P2 背鍵替代操作

P1／P2 背鍵目前不進入 ROS 作為獨立按鍵；`evtest` 實測 P1／P2 沒有獨立事件。實機操作
採用 8BitDo 軟體 remap：

```text
P1 = R3
P2 = L3
```

因此 `horizontal_joystick_bridge_node` 不需要改動，仍只讀取 `msg.l3` 和 `msg.r3`：

```text
P1 -> R3 -> STAFF mode Motor7 inclination/head relay
P2 -> L3 -> STAFF mode Motor8 inclination/head relay
KFS mode 下 P1/P2 不控制 Motor6；Motor6 horizontal 由 L2/R2 控制
```

此配置只影響操作者手感，不改變 topic、message、timeout、Motor6 controller 或 Damiao
控制鏈路。若未來某個手柄模式能讓 P1／P2 產生獨立 evdev code，才需要擴充
`my_joystick_msgs/msg/Joystick.msg` 與 `my_joystick_driver/joystick_node.py`。


## 2026-06-19 STAFF/KFS operation mode 鍵位更新

本節取代前文「START 在 Motor7/Motor8 之間切換」的現行行為；舊內容保留作歷史回溯。

`motor_position_selector_joystick_bridge_node` 現在訂閱 `/operation_mode` (`std_msgs/msg/Int32`)：

```text
0 = INVALID，禁用 staff position 按鍵
1 = STAFF，啟用 Motor7/8 staff position 按鍵
2 = KFS，禁用 staff position 按鍵
```

STAFF mode 下位置速度模式鍵位：

```text
X  -> Motor8 staff gripper preset/open-close cycle
B  -> Motor7 staff gripper preset/open-close cycle
L2 -> Motor8 manual trim，負方向，按壓深度 0..1
R2 -> Motor7 manual trim，正方向，按壓深度 0..1
```

`/motor7_position_input` 與 `/motor8_position_input` 格式仍為 `[toggle_event, trim_input, input_valid]`。mode 不是 STAFF、`/operation_mode` 超過 `mode_timeout_sec=0.5 s` 未更新、或 `/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時，bridge 發布 `[0,0,0]`，position controller 停止接收 toggle/trim 並以自身安全邏輯保持/回到當前位置。

`elevator_joystick_bridge_node` 沒有 `enabled` 參數；它靠 `/operation_mode=2` 且 mode 未超時來啟用 KFS elevator 控制。STAFF mode 下 L1/R1 不會送 elevator speed。


## 2026-06-19 KFS mode elevator/horizontal 鍵位

本節補充 STAFF/KFS operation mode：`elevator_joystick_bridge_node` 與 `horizontal_joystick_bridge_node` 現在也訂閱 `/operation_mode`，只有 KFS mode (`2`) 且 mode topic 未超過 `mode_timeout_sec=0.5 s` 時才接受按鍵。

KFS mode 鍵位：

```text
L1 -> Motor5 elevator negative/down
R1 -> Motor5 elevator positive/up
L2 -> Motor6 horizontal negative/in
R2 -> Motor6 horizontal positive/out
```

若實機方向與「出/入、升/降」相反，只需要交換符號或按鍵映射，不影響 topic 介面。

STAFF mode 下 L1/R1 仍交給 pneumatic head toggle，L2/R2 仍交給 Motor8/Motor7 position trim；因此 elevator/horizontal bridge 在 STAFF mode 會發布 `0.0`。


## 2026-06-19 STAFF mode A/Y 90-degree 與 L/R 微調更新

本節取代前文 `X/B` 控 Motor8/Motor7 preset、`L2/R2` 控微調的現行鍵位說明。

STAFF mode 最新位置速度模式鍵位：

```text
Y  -> Motor7 preset / left-right 90-degree cycle
A  -> Motor8 preset / left-right 90-degree cycle
R1 -> Motor7 trim negative
R2 -> Motor7 trim positive
L1 -> Motor8 trim negative
L2 -> Motor8 trim positive
```

`B` 不再由 staff position bridge 使用，避免和現有 90-degree turn 行為衝突。`X` 目前也不再由 staff position bridge 使用。

KFS mode horizontal 方向已對調：

```text
L2 -> Motor6 horizontal positive/out
R2 -> Motor6 horizontal negative/in
```


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


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 r1_arm_control 現行 mode gate 與按鍵

`r1_arm_control` 目前只負責 Motor5/Motor6/Motor7/Motor8 的 ROS 控制與手柄 bridge，不直接處理 Arduino relay。

- `motor_position_selector_joystick_bridge_node` 只在 `/operation_mode=1` 且 mode 未超時時工作：`A -> /motor7_position_input toggle`，`X -> /motor8_position_input toggle`，`R1/R2 -> Motor7 trim -/+`，`L1/L2 -> Motor8 trim -/+`。
- `horizontal_joystick_bridge_node` 只在 `/operation_mode=2` 且 mode 未超時時工作：`L2 -> positive/out`，`R2 -> negative/in`。
- `elevator_joystick_bridge_node` 只在 `/operation_mode=2` 且 mode 未超時時工作：`L1 -> negative/down`，`R1 -> positive/up`。
- `/operation_mode` 超過 `mode_timeout_sec=0.5 s` 或 `/joystick_data` 超過 `input_timeout_sec=0.3 s` 後，各 bridge 發布停止/invalid 輸出，避免舊按鍵狀態繼續控制機構。

## 2026-06-19 Motor5 elevator current KFS mechanism speed update

Motor5 elevator and Motor6 horizontal current default speeds are:

```text
elevator_joystick_bridge_node.command_speed_rad_s = 28.0 rad/s
elevator_controller_node.max_speed_rad_s = 28.0 rad/s
```

Both values must match the intended maximum. The joystick bridge publishes `/elevator_speed_cmd=[+/-28.0]` in KFS mode, and the controller clamps any incoming command to `max_speed_rad_s`. If only the bridge is changed but the controller remains at `3.0`, the real command sent to `/damiao_control` will still be limited to `3.0 rad/s`.

Safety behavior is unchanged: `/operation_mode` must be KFS (`2`), mode timeout still disables L1/R1 input, and `elevator_controller_node.timeout_sec=0.3 s` still sends `0 rad/s` when `/elevator_speed_cmd` stops refreshing. `max_accel_rad_s2` remains `0.0`, so there is no extra elevator ramp unless that parameter is set later.

## 2026-06-20 KFS mechanism speed parameters

This section is the current source for Motor5/Motor6 speed parameters inside `r1_arm_control`.

```text
Motor5 elevator:
  elevator_joystick_bridge_node.command_speed_rad_s = 28.0 rad/s
  elevator_controller_node.max_speed_rad_s = 28.0 rad/s
  buttons: KFS mode L1 negative/down, R1 positive/up

Motor6 horizontal:
  horizontal_joystick_bridge_node.command_speed_rad_s = 30.0 rad/s
  horizontal_controller_node.max_speed_rad_s = 30.0 rad/s
  buttons: KFS mode L2 positive/out, R2 negative/in
```

The bridge value and controller max value must match the intended command. If the bridge publishes a higher speed but the controller max remains lower, `/damiao_control` will still be clamped by the controller. Timeout behavior is unchanged: both controllers use `timeout_sec=0.3 s` and publish `0 rad/s` when their command topic stops refreshing. Both controllers still have `max_accel_rad_s2=0.0`, so there is no extra ramp on Motor5/Motor6 unless that parameter is set later.

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
