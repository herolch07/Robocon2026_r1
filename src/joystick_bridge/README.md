# Joystick Bridge Node

## 📅 Changelog

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
| `max_speed_cm` | float | 100.0 | 最大平移速度 (cm/s) |
| `max_rotation` | float | 2.0 | 最大旋转速度 (rad/s) |
| `deadzone` | int | 410 | 摇杆死区阈值 (对应 ±8192 范围) |

---

## 🎮 控制映射

### 左摇杆 (lx, ly)
- **X 轴 (lx)**: 控制运动方向（-8192 到 8192）
- **Y 轴 (ly)**: 控制平移速度大小（-8192 到 8192）
- **映射关系**:
  - 方向角 = atan2(lx, -ly) （注意 Y 轴取反）
  - 速度大小 = sqrt(lx² + ly²) / 8192 × max_speed

### 右摇杆 (rx)
- **X 轴 (rx)**: 控制旋转速度（-8192 到 8192）
- **映射关系**: rotation = rx / 8192 × max_rotation

### 死区处理
当摇杆值小于 `deadzone` 时，视为回中状态：
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
  -p max_rotation:=3.0 \
  -p deadzone:=500
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
```
[DEBUG] Joy: lx=4096, ly=-8192, rx=0 → Nav: dir=150.0°, speed=100.0cm/s, rot=0.00rad/s
[WARN] Invalid joystick command: expected 8 fields, got 5
```

---

## 📋 未来改进计划

### 已规划功能
- [ ] 支持按键映射（如 A/B 键切换速度档位）
- [ ] 添加速度档位调节（低/中/高速）
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
