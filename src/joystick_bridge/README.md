> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# Joystick Bridge Node

## 📅 Changelog

### v1.10.0 (2026-06-20)
**右搖桿旋轉上限提高到 3.0 rad/s**
- `max_rotation` 当前默认值为 `3.0 rad/s`。
- 旋转曲线仍为 `y = 0.1x + 0.9x³`。
- 满杆可请求 `3.0 rad/s`，但平移+旋转组合仍可能被 `local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s` 同比缩放。
- topic、deadzone、watchdog 和 D-pad KFS 視角邏輯不變。

### v1.9.0 (2026-06-07)
**右摇杆旋转加入混合三次曲线并提高最大速度**
- `max_rotation` 在此版本當時從 `0.5` 改為 `1.2 rad/s`；目前預設值請以 v1.10.0 的 `3.0 rad/s` 為準。
- 新增 `rotation_linear_weight = 0.1`。
- 右搖桿使用 `y = 0.1x + 0.9x³`，小推桿便於微操；此版本當時滿桿為 `1.2 rad/s`。
- topic、`deadzone = 15` 和 `input_timeout_sec = 0.3 s` watchdog 均保持不变。

### v1.8.0 (2026-06-07)
**提高底盘低速微操精度**
- `translation_linear_weight` 默认从 `0.2` 改为 `0.1`。
- 左摇杆平移曲线更新为 `y = 0.1x + 0.9x³`。
- `max_speed_cm = 150.0 cm/s`、`deadzone = 15`、右摇杆旋转和 watchdog 均保持不变。
- 旧版 `0.2` 曲线说明作为历史设计记录保留。

### v1.7.0 (2026-06-07)
**底盘摇杆 deadzone 降至约 3%**
- `deadzone` 默认从 `24` 改为 `15`。
- 摇杆范围保持 `-512..512`，因此实际比例为 `15/512 = 2.93%`。
- `my_joystick_driver` 与 `joystick_bridge` 两层同步修改，避免上游仍过滤 `±24`。
- Motor 7 的 L2/R2 使用独立 `trigger_deadzone = 24`，本次不变。

### v1.6.0 (2026-06-06)
**固定 150 cm/s + 混合三次平移曲线**
- `max_speed_cm` 默认改为 `150.0 cm/s`。
- 左摇杆平移幅度使用 `y = 0.2x + 0.8x³`，其中 `x` 为归一化摇杆幅度。
- 移除 START/SELECT 底盘速度档切换；两个按钮当前不参与底盘控制。
- 新增参数 `translation_linear_weight = 0.2`，允许在 `0.0..1.0` 范围调节曲线。
- 右摇杆旋转仍为线性映射，`max_rotation = 0.5 rad/s`。
- `/joystick_data` timeout watchdog 和底层 `max_wheel_accel_rad_s2` 不变。

### v1.5.0 (2026-05-28)
**确认 R1/R2 ROS domain 混线后恢复 150 cm/s 默认最高档**
- 已确认异常根因是 R1 能看到 R2 的 ROS2 node / topic，而不是 joystick `128/512` 映射。
- R1 启动脚本已固定 `ROS_DOMAIN_ID=1` 与 `ROS_LOCALHOST_ONLY=1`，避免再次被 R2 graph 影响。
- 默认 `speed_levels_cm` 设置为 `[10, 20, 40, 60, 100, 150]`，继续按较安全速度路线测试。
- 當時 `local_navigation_node max_wheel_speed_rad_s` 保持 `64.0 rad/s`；目前 source 預設為 `40.0 rad/s`。

### v1.4.0 (2026-05-27)
**恢复上一版速度档位用于复测**
- 用户更换 board 后问题仍存在，因此恢复 `speed_levels_cm` 到 `[10, 20, 60, 100, 200, 400]` 用于对比测试。
- 本次未修改 `local_navigation_node max_wheel_speed_rad_s`、watchdog、左摇杆映射或运动学参数。

### v1.3.0 (2026-05-27)
**200 cm/s 实机触发保护后的速度档位调整**
- 实机测试中 `200 cm/s` 档位导致底盘突然断反应，疑似触发电源或驱动器保护。
- 當時不修改 `local_navigation_node max_wheel_speed_rad_s`，仍保持 `64.0 rad/s`；目前 source 預設為 `40.0 rad/s`。
- 默认 `speed_levels_cm` 改为 `[10, 20, 40, 60, 100, 150]`，controller 最高档暂定 `150 cm/s`。

### v1.2.0 (2026-05-25)
**手柄速度档位切换与 400 cm/s 最大速度准备**
- 新增 `speed_levels_cm`，默认 `[10, 20, 60, 100, 200, 400]`
- 新增 `speed_level_index`，默认 `0`，启动时从 `10 cm/s` 精细低速档开始
- `START` 按键升高底盘平移速度档位
- `SELECT` 按键降低底盘平移速度档位
- `max_speed_cm` 仍是当前实际用于 `/local_driving` 的平移速度上限

### v1.1.0 (2026-05-16)
**降低右摇杆默认旋转速度**
- `max_speed_cm` 默认值从 `40.0 cm/s` 降到 `20.0 cm/s`
- `max_rotation` 默认值从 `2.0 rad/s` 降到 `0.5 rad/s`
- 目的：降低横向、斜向、原地旋转联调时的电流冲击
- 接口不变，仍通过 `/local_driving` 发布 `[direction_rad, speed_cm/s, rotation_rad/s]`
- `input_timeout_sec = 0.3 s` watchdog 安全行为不变

### v1.0.0 (2026-01-30)
**初始版本：手柄到底盘控制桥接节点**
- 实现手柄数据到全向底盘导航指令的转换
- 支持左摇杆控制平移方向和速度
- 支持右摇杆控制旋转速度
- 死区过滤防止微小漂移
- 符合 AGENTS.md 工程规范

---

## 🎯 节点功能说明

### 节点名称
`joystick_bridge`

### 职责（符合 AGENTS.md 2.1 规范）
专用于将手柄输入转换为全向底盘运动指令，绑定特定的机械结构（4轮X型全向底盘）。

### 适用范围
- 适用于使用 `my_joystick_msgs/Joystick` 消息格式的手柄
- 适用于接受 `std_msgs/Float32MultiArray` 格式的全向底盘导航节点
- 适用于 4 轮 X 型布局的全向底盘（如 R2 机器人）

---

## 🔌 接口设计

### 订阅的话题
| 话题名 | 消息类型 | 频率 | 说明 |
|--------|---------|------|------|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | 20Hz | 手柄输入数据 |

### 发布的话题
| 话题名 | 消息类型 | 频率 | 说明 |
|--------|---------|------|------|
| `/local_driving` | `std_msgs/msg/Float32MultiArray` | 按需 | 底盘导航指令 |

### 参数配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_speed_cm` | float | 150.0 | 满杆最大平移目标速度 (cm/s) |
| `max_rotation` | float | 3.0 | 右摇杆满杆最大旋转速度 (rad/s) |
| `deadzone` | int | 15 | 摇杆死区阈值，约为 ±512 满量程的 2.93% |
| `input_timeout_sec` | float | 0.3 | `/joystick_data` 输入超时时间 (s) |
| `watchdog_hz` | float | 20.0 | 输入 watchdog 检查频率 (Hz) |
| `translation_linear_weight` | float | 0.1 | 平移混合曲线线性权重，范围 `0.0..1.0` |
| `rotation_linear_weight` | float | 0.1 | 旋转混合曲线线性权重，范围 `0.0..1.0` |

---

## 🎮 控制映射

### 左摇杆 (lx, ly)
- **X 轴 (lx)**: 控制运动方向（-512 到 512）
- **Y 轴 (ly)**: 控制平移速度大小（-512 到 512）
- **映射关系**:
  - 方向角 = atan2(lx, -ly) （注意 Y 轴取反）
  - 原始幅度 `x = min(sqrt(lx² + ly²) / 512, 1.0)`
  - 曲线幅度 `y = 0.1x + 0.9x³`
  - 速度 `speed = y × 150 cm/s`

### 右摇杆 (rx)
- **X 轴 (rx)**: 控制旋转速度（-512 到 512）
- **映射关系**：`x = clamp(rx / 512, -1, 1)`，`rotation = (0.1x + 0.9x³) × 3.0 rad/s`

### START / SELECT
- 当前不用于底盘速度切换。
- 底盘平移上限默认固定为 `150 cm/s`。
- 低速精细控制由左、右摇杆各自的混合三次曲线提供。

### 死区处理
当摇杆绝对值小于 `deadzone` 时，视为回中状态：
- 平移速度置零
- 仅保留旋转分量（如果有的话）

---

## 🏗️ 系统架构

```
[手柄硬件] 
    ↓
[joystick_node] (发布 /joystick_data)
    ↓
[joystick_bridge] ← 本节点
    ↓
[local_navigation_node] (订阅 /local_driving)
    ↓
[damiao_node] (发布 /damiao_control)
    ↓
[4× DM 电机]
```

---

## 🚀 启动方式

### 方法 1：直接运行
```bash
# 确保已编译工作空间
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --packages-select joystick_bridge
source install/setup.bash

# 启动节点
ros2 run joystick_bridge joystick_bridge
```

### 方法 2：使用参数配置
```bash
ros2 run joystick_bridge joystick_bridge --ros-args \
  -p max_speed_cm:=150.0 \
  -p translation_linear_weight:=0.1 \
  -p max_rotation:=3.0 \
  -p rotation_linear_weight:=0.1 \
  -p deadzone:=15
```

曲线调节示例（`1.0` 为完全线性，`0.0` 为纯三次）：

```bash
ros2 param set /joystick_bridge translation_linear_weight 0.3
ros2 param set /joystick_bridge rotation_linear_weight 0.3
```

### 方法 3：与其它节点一起启动
```bash
# 终端 1: 手柄驱动
ros2 run my_joystick_driver joystick_node

# 终端 2: 转换节点
ros2 run joystick_bridge joystick_bridge

# 终端 3: 底盘控制
ros2 run base_omniwheel_r2_700 damiao_node

# 终端 4: 导航节点
ros2 run base_omniwheel_r2_700 local_navigation_node
```

---

## 🔧 调试方法

### 查看输入数据
```bash
# 查看手柄原始数据
ros2 topic echo /joystick_data

# 查看转换后的导航指令
ros2 topic echo /local_driving
```

### 查看节点状态
```bash
# 查看节点信息
ros2 node info /joystick_bridge

# 查看话题连接
ros2 topic info /joystick_data
ros2 topic info /local_driving
```

### 性能监控
```bash
# 查看话题发布频率
ros2 topic hz /local_driving

# 查看节点日志
ros2 run joystick_bridge joystick_bridge --ros-args --log-level debug
```

---

## ⚠️ 超时保护机制

### 已实现的保护（符合 AGENTS.md 9.1 规范）

**输入超时检测：**
- 本节点作为订阅者，无法主动检测发布者超时
- 依赖上游 `joystick_node` 的超时保护机制
- 如果手柄断开，`joystick_node` 会发布全零数据

**输出安全处理：**
- 接收到全零手柄数据时，输出停止指令
- 无效数据会记录警告日志并忽略

**日志输出：**
```text
[DEBUG] Joy: lx=256, ly=-512, rx=0 -> Nav: dir=26.6deg, speed=150.0cm/s, rot=0.00rad/s
[WARN] Invalid joystick command: expected Joystick message fields
```

---

## 📋 未来改进计划

### 已完成功能
- [x] 历史版本支持 START/SELECT 速度档；v1.6.0 已取消
- [x] 固定默认上限 150 cm/s，并使用混合三次曲线提供低速控制

### 已规划功能
- [ ] 支持紧急停止按钮映射
- [ ] 添加手柄连接状态指示

### 性能优化
- [ ] 降低 CPU 占用率
- [ ] 优化数据转换算法
- [ ] 添加消息队列长度监控

---

## 📄 许可证

Apache License 2.0

## 👥 维护者

EdUHK Robocon Robotics Team

---

## 2026-05-14 安全更新：输入 Watchdog

本节是对旧版“超时保护机制”的追加说明。旧版设计主要依赖上游 `joystick_node` 发布全零数据；当前版本已经在 `joystick_bridge` 内增加主动输入 watchdog。

### 超时触发条件

```text
超过 input_timeout_sec 没有收到新的 /joystick_data
```

默认参数：

```text
input_timeout_sec = 0.3 s
watchdog_hz = 20.0 Hz
```

### 超时后的行为

节点向 `/local_driving` 发布一次停止指令：

```text
data = [0.0, 0.0, 0.0]
```

含义：

```text
direction_rad = 0.0
speed_cm_per_sec = 0.0
rotation_rad_per_sec = 0.0
```

这样即使手柄驱动、USB 手柄或上游 topic 链路异常，底盘上层运动指令也会回到安全状态。

### 调整方式

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param set /joystick_bridge input_timeout_sec 0.3
ros2 param get /joystick_bridge watchdog_hz
```

## 2026-05-25 - v1.2.0 速度档位操作说明

当前手柄速度档位：

```text
10 cm/s -> 20 cm/s -> 40 cm/s -> 60 cm/s -> 100 cm/s -> 150 cm/s
```

操作：

```text
START: 升高一档
SELECT: 降低一档
```

查看当前档位对应速度：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge speed_level_index
```

注意：本段是旧速度档历史记录。当前 source 默认不再使用 START/SELECT 速度档；`max_speed_cm=150.0 cm/s`，`local_navigation_node max_wheel_speed_rad_s=40.0 rad/s`。

## 2026-06-06 - v1.6.0 历史控制方式

```text
max_speed_cm = 150.0 cm/s
translation_linear_weight = 0.2
曲线: y = 0.2x + 0.8x^3
START/SELECT: 不再调整底盘速度
```

当时的摇杆幅度和目标速度示例：

| 摇杆幅度 | 输出速度 |
|---:|---:|
| 10% | 3.12 cm/s |
| 25% | 9.38 cm/s |
| 50% | 30.00 cm/s |
| 75% | 73.13 cm/s |
| 100% | 150.00 cm/s |

`input_timeout_sec = 0.3 s` watchdog 不变；超时后仍发布 `/local_driving = [0,0,0]`。

## 2026-06-07 当前 Deadzone

```text
joystick axis range = -512..512
deadzone = 15（约 2.93%）
abs(axis) < 15 -> 视为 0
abs(axis) >= 15 -> 进入控制计算
```

## 2026-06-07 - v1.8.0 当前平移曲线

```text
max_speed_cm = 150.0 cm/s
translation_linear_weight = 0.1
曲线: y = 0.1x + 0.9x^3
START/SELECT: 不调整底盘速度
```

理论目标速度：

| 摇杆幅度 | 输出速度 |
|---:|---:|
| 10% | 1.64 cm/s |
| 25% | 5.86 cm/s |
| 50% | 24.38 cm/s |
| 75% | 68.20 cm/s |
| 100% | 150.00 cm/s |

`input_timeout_sec = 0.3 s` watchdog 不变；超时后仍发布 `/local_driving = [0,0,0]`。

## 2026-06-07 - v1.9.0 当前旋转曲线

```text
max_rotation = 3.0 rad/s
rotation_linear_weight = 0.1
曲线: y = 0.1x + 0.9x^3
```

| 右摇杆幅度 | 旋转速度 |
|---:|---:|
| 10% | 0.033 rad/s |
| 25% | 0.117 rad/s |
| 50% | 0.488 rad/s |
| 75% | 1.364 rad/s |
| 100% | 3.000 rad/s |

`input_timeout_sec = 0.3 s` watchdog 不变；超时后仍发布 `/local_driving = [0,0,0]`。


## 2026-06-14 v2.0 手動人視角座標

本節取代舊版「左搖桿固定使用車體座標」的目前行為說明；舊章節保留作版本回溯。

十字鍵現在用於指定 E-stop（Motor1／2 中間的車頭）在人視角中的絕對方向：

```text
十字鍵上：E-stop 在人的前方，view=0
十字鍵右：E-stop 在人的右方，view=1
十字鍵下：E-stop 在人的後方，view=2
十字鍵左：E-stop 在人的左方，view=3
```

左搖桿先按人的固定視角解讀，再轉換為車體座標。右搖桿旋轉不受影響。為避免移動中
方向瞬間跳變，預設只有左搖桿回中時才接受新的十字鍵方向；被拒絕後需要鬆開十字鍵，
待左搖桿回中後重新按下。

新增發布：

| Topic | 類型 | 內容 |
|---|---|---|
| `/view_orientation` | `std_msgs/msg/Int32` | `0=前、1=右、2=後、3=左` |

新增參數：

| 參數 | 預設值 | 作用 |
|---|---:|---|
| `default_view_orientation` | `0` | 節點啟動時 E-stop 在人視角中的方向 |
| `view_change_requires_neutral` | `true` | 是否要求左搖桿回中才允許改變視角 |

`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時仍發布
`/local_driving=[0,0,0]`。視角狀態不會自動推算，重啟節點後回到預設 `0`；每次車身轉過
90 度或操作人改變站位後，必須手動按十字鍵同步。


## 2026-06-19 v2.1 KFS gripper 作為人視角基準

本節取代 v2.0 中「十字鍵指定 E-stop／車頭方向」的現行操作說明；v2.0 保留作歷史記錄。

十字鍵現在指定 **KFS gripper 在操作人視角中的絕對方向**，不是指定 E-stop 方向：

```text
十字鍵上：KFS gripper 在人的前方，view=0
十字鍵右：KFS gripper 在人的右方，view=1
十字鍵下：KFS gripper 在人的後方／靠近人，view=2
十字鍵左：KFS gripper 在人的左方，view=3
```

目前機械幾何假設：當 E-stop／車體前方在人視角前方時，KFS gripper 在人視角左方。
因此 `joystick_bridge` 內部使用 `E-stop view = (KFS view + 1) % 4` 轉換後，再把左搖桿的人視角方向轉成車體座標。

預設 `default_view_orientation=2`，對應開機時 KFS gripper 朝向操作人。`/view_orientation` 發布的也是 KFS gripper 方向，仍為 `0=前、1=右、2=後、3=左`。

安全與超時策略不變：左搖桿未回中時拒絕切換視角；`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時發布 `/local_driving=[0,0,0]`。


## 2026-06-19 v2.2 KFS gripper 作為車頭標

本節取代 v2.1 中 `E-stop view = (KFS view + 1) % 4` 的現行假設；v2.1 保留作回溯記錄。

目前操作基準改為：**KFS gripper 就是操作者用來判斷車頭／機器前方的視覺標記**。因此十字鍵指定的是 KFS gripper，也同時等同於車體前方在人視角中的方向：

```text
十字鍵上：KFS gripper／車頭 在人的前方，view=0
十字鍵右：KFS gripper／車頭 在人的右方，view=1
十字鍵下：KFS gripper／車頭 在人的後方／靠近人，view=2
十字鍵左：KFS gripper／車頭 在人的左方，view=3
```

內部轉換簡化為 `body_front_view = KFS view`，不再額外加 90 度或 180 度偏移。預設仍為 `default_view_orientation=2`，對應開機時 KFS gripper 朝向操作人。

安全與超時策略不變：左搖桿未回中時拒絕切換視角；`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時發布 `/local_driving=[0,0,0]`。


## 2026-06-19 v2.3 KFS gripper 開機預設在前方

本節取代 v2.2 中 `default_view_orientation=2` 的現行預設說明；v2.2 保留作回溯記錄。

目前開機預設改為 `default_view_orientation=0`，等同於 D-pad 上。也就是節點啟動後假設 KFS gripper／車頭在人視角前方。`/view_orientation` 啟動後應發布 `0`。

方向語義不變：KFS gripper 仍直接視為車體前方／車頭標，內部仍使用 `body_front_view = KFS view`。左搖桿未回中時仍拒絕切換視角；`/joystick_data` 超過 `input_timeout_sec=0.3 s` 未更新時仍發布 `/local_driving=[0,0,0]`。


## 2026-06-19 v2.4 KFS front-marker 90-degree calibration

This section supersedes v2.3 for the active conversion formula. Real-machine testing showed that when the KFS gripper is visually at the front, pressing D-pad left made left-stick-forward move forward in the operator view, while D-pad up made the chassis move left. That means the chassis body-frame forward axis is offset by 90 degrees from the visible KFS marker.

The active conversion is therefore:

```text
body_front_view = (KFS view - 1) % 4
```

The D-pad semantic remains unchanged: D-pad up still means KFS gripper is visually in front of the operator. Startup default remains `default_view_orientation=0`, equivalent to D-pad up. With this calibration, startup view `0` should make left-stick-forward move forward in the operator view when the KFS gripper is visually at the front.

Timeout behavior is unchanged: if `/joystick_data` is stale for `input_timeout_sec=0.3 s`, the node publishes `/local_driving=[0,0,0]`.


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 KFS visual front D-pad 底盤視角

`joystick_bridge` 的 D-pad 現在不控制機構，也不直接令底盤旋轉。D-pad 只更新 KFS visual front 在機手視角中的方向，左搖桿再根據該方向轉換為底盤 body frame 速度。

目前實機校正公式：

```text
body_front_view = (KFS view - 1) % 4
```

開機預設 `view=0`，等同 D-pad Up。更新 D-pad 前左搖桿需要回中，避免高速移動中突然切換人視角造成方向突變。

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

## 2026-06-20 Current Rotation Default

Current source default:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

Older sections mentioning `1.2 rad/s` or `2.4 rad/s` are historical and are not the current runtime default.

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
