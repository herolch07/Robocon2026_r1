# Joystick Bridge Node

## 📅 Changelog

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
- `local_navigation_node max_wheel_speed_rad_s` 保持 `64.0 rad/s` 不变。

### v1.4.0 (2026-05-27)
**恢复上一版速度档位用于复测**
- 用户更换 board 后问题仍存在，因此恢复 `speed_levels_cm` 到 `[10, 20, 60, 100, 200, 400]` 用于对比测试。
- 本次未修改 `local_navigation_node max_wheel_speed_rad_s`、watchdog、左摇杆映射或运动学参数。

### v1.3.0 (2026-05-27)
**200 cm/s 实机触发保护后的速度档位调整**
- 实机测试中 `200 cm/s` 档位导致底盘突然断反应，疑似触发电源或驱动器保护。
- 不修改 `local_navigation_node max_wheel_speed_rad_s`，仍保持 `64.0 rad/s`。
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
| `max_rotation` | float | 0.5 | 最大旋转速度 (rad/s) |
| `deadzone` | int | 24 | 摇杆死区阈值 (对应 ±512 范围) |
| `input_timeout_sec` | float | 0.3 | `/joystick_data` 输入超时时间 (s) |
| `watchdog_hz` | float | 20.0 | 输入 watchdog 检查频率 (Hz) |
| `translation_linear_weight` | float | 0.2 | 混合曲线线性权重，范围 `0.0..1.0` |

---

## 🎮 控制映射

### 左摇杆 (lx, ly)
- **X 轴 (lx)**: 控制运动方向（-512 到 512）
- **Y 轴 (ly)**: 控制平移速度大小（-512 到 512）
- **映射关系**:
  - 方向角 = atan2(lx, -ly) （注意 Y 轴取反）
  - 原始幅度 `x = min(sqrt(lx² + ly²) / 512, 1.0)`
  - 曲线幅度 `y = 0.2x + 0.8x³`
  - 速度 `speed = y × 150 cm/s`

### 右摇杆 (rx)
- **X 轴 (rx)**: 控制旋转速度（-512 到 512）
- **映射关系**: rotation = rx / 512 × max_rotation

### START / SELECT
- 当前不用于底盘速度切换。
- 底盘平移上限默认固定为 `150 cm/s`。
- 低速精细控制由左摇杆混合三次曲线提供。

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
cd /home/robotics/robocon/new_ws
colcon build --packages-select joystick_bridge
source install/setup.bash

# 启动节点
ros2 run joystick_bridge joystick_bridge
```

### 方法 2：使用参数配置
```bash
ros2 run joystick_bridge joystick_bridge --ros-args \
  -p max_speed_cm:=150.0 \
  -p translation_linear_weight:=0.2 \
  -p max_rotation:=0.5 \
  -p deadzone:=24
```

曲线调节示例（`1.0` 为完全线性，`0.0` 为纯三次）：

```bash
ros2 param set /joystick_bridge translation_linear_weight 0.3
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

注意：`150 cm/s` 是当前 controller 默认最高档。`200/400 cm/s` 仍可通过参数临时测试，但不再作为默认按钮档位；`local_navigation_node max_wheel_speed_rad_s` 保持 `64.0 rad/s`。

## 2026-06-06 - v1.6.0 当前控制方式

```text
max_speed_cm = 150.0 cm/s
translation_linear_weight = 0.2
曲线: y = 0.2x + 0.8x^3
START/SELECT: 不再调整底盘速度
```

摇杆幅度和目标速度示例：

| 摇杆幅度 | 输出速度 |
|---:|---:|
| 10% | 3.12 cm/s |
| 25% | 9.38 cm/s |
| 50% | 30.00 cm/s |
| 75% | 73.13 cm/s |
| 100% | 150.00 cm/s |

`input_timeout_sec = 0.3 s` watchdog 不变；超时后仍发布 `/local_driving = [0,0,0]`。
