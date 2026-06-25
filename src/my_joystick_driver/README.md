> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# My Joystick Driver

ROS 2 手柄驱动节点，将物理手柄输入转换为标准化的 ROS2 消息。

## 📅 Changelog

### v1.0.0 (2026-01-30)
**初始版本：符合 AGENTS.md 工程规范**
- ✅ 实现 evdev 底层手柄数据读取
- ✅ 支持参数化设备配置（自动检测/手动指定）
- ✅ 数据归一化到 ±512 范围，trigger 为 0~512
- ✅ 死区过滤防止摇杆漂移
- ✅ 断线自动归零保护机制
- ✅ 详细的设备调试信息
- ✅ 支持多种手柄品牌（8BitDo, Xbox, PS5 等）

---

## 🎯 节点功能说明

### 节点名称
`joystick_node`

### 职责（符合 AGENTS.md 2.1 规范）
专用于读取物理手柄硬件输入并发布标准化 ROS2 消息，绑定特定的输入设备接口。

### 适用范围
- 适用于 Linux 系统下的 USB/蓝牙手柄设备
- 支持 evdev 兼容的所有手柄
- 适用于需要手柄输入的任何 ROS2 机器人系统

---

## 🔌 接口设计

### 发布的话题
| 话题名 | 消息类型 | 频率 | 说明 |
|--------|---------|------|------|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | 20Hz | 手柄的实时状态数据 |

### 参数配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `auto_detect` | bool | `true` | 是否自动检测手柄设备 |
| `device_path` | string | `""` | 手动指定设备路径（需 `auto_detect=false`） |
| `device_name_filter` | string | `"8BitDo"` | 自动检测时的设备名称过滤器 |

---

## 🎮 控制映射

### 模拟轴（归一化为整数）
- `lx`, `ly`: 左摇杆 X/Y 轴（-512 到 512）
- `rx`, `ry`: 右摇杆 X/Y 轴（-512 到 512）
- `dx`, `dy`: 方向键 X/Y 轴（-512, 0, 512）
- `l2`, `r2`: 左/右扳机（0 到 512）

### 数字按键（布尔值）
- `a`, `b`, `x`, `y`: 四个主要按键
- `l1`, `r1`: 左/右肩键
- `l3`, `r3`: 左/右摇杆按下
- `select`, `start`: 选择/开始键

---

## ⚠️ 超时保护机制（符合 AGENTS.md 9.1 规范）

### 已实现的保护机制

**1. 硬件断连检测与超时处理**

- **触发条件：** 
  - `OSError` 异常（设备文件 `/dev/input/eventX` 不可读）
  - 通常发生在手柄物理断开、电量耗尽或蓝牙连接丢失时

- **检测机制：**
  - 事件驱动型（实时检测，无延迟）
  - 在后台线程的 `read_loop()` 中捕获异常

- **超时后的行为：**
  1. 立即调用 `_reset_states()`，将所有摇杆和按键状态归零
  2. 发布一条"全零"消息到 `/joystick_data`
  3. 关闭设备句柄（`self.gamepad.close()`）
  4. 进入 2 秒等待后重新尝试连接

- **日志输出：**
  ```
  [ERROR] [joystick_node]: Joystick OSError: {e}. Device may be disconnected.
  [INFO] [joystick_node]: Joystick states reset to safety (all zeros)
  ```

**2. 节点关闭保护**

- **触发条件：** 
  - 节点被 Ctrl+C 终止
  - `destroy_node()` 被调用

- **行为：**
  1. 调用 `_reset_states()` 归零所有状态
  2. 取消发布定时器
  3. 关闭设备连接
  4. 清理资源

---

## 🚀 启动方式

### 方法 1：自动检测模式（默认，推荐）
```bash
ros2 run my_joystick_driver joystick_node
```

### 方法 2：使用其他品牌手柄
```bash
ros2 run my_joystick_driver joystick_node --ros-args -p device_name_filter:="Xbox"
```

### 方法 3：手动指定设备路径
```bash
ros2 run my_joystick_driver joystick_node --ros-args -p auto_detect:=false -p device_path:="/dev/input/event5"
```

---

## 🔧 调试方法

### 查看实时数据
```bash
ros2 topic echo /joystick_data
```

### 查看参数
```bash
ros2 param list /joystick_node
ros2 param get /joystick_node auto_detect
```

### 查看设备列表（连接失败时自动显示）
当设备连接失败时，节点会自动打印所有可用的输入设备信息。

---

## 📋 未来改进计划

### 已规划功能
- [ ] 支持按键组合映射
- [ ] 添加震动反馈支持
- [ ] 实现配置文件持久化
- [ ] 添加连接状态 LED 指示

### 性能优化
- [ ] 优化事件处理循环
- [ ] 减少不必要的状态发布
- [ ] 添加性能监控指标

---

## 📄 许可证

Apache License 2.0

## 👥 维护者

EdUHK Robocon Robotics Team

## 2026-06-07 摇杆 Deadzone 更新

- 四个摇杆轴归一化范围保持 `-512..512`。
- 默认 deadzone 从 `24` 改为 `15`，即约 `2.93%`。
- L2/R2 虽经过 driver 的基础过滤，但 Motor 7 bridge 仍使用独立 `trigger_deadzone = 24`。

## 2026-06-10 evdev 运行依赖修复

- `package.xml` 新增 `python3-evdev` 运行依赖，允许 `rosdep` 安装节点所需的 Linux 输入设备库。
- `setup.py` 新增 Python package 依赖 `evdev`，避免生成的 package 元数据遗漏直接依赖。
- Ubuntu 24.04 推荐使用系统包安装，确保依赖进入 ROS 2 使用的 `/usr/bin/python3`：

```bash
sudo apt update
sudo apt install python3-evdev
```

- 安装后重新构建并加载 workspace：

```bash
colcon build --packages-select my_joystick_driver
source install/setup.bash
ros2 run my_joystick_driver joystick_node
```

- 若出现 `/dev/input/event*` 权限错误，将当前用户加入 `input` 组后重新登录：

```bash
sudo usermod -aG input "$USER"
```

## 2026-06-11 8BitDo 主/后备手柄自动检测白名单

RSP 实机确认支持以下两个 evdev 名称：

```text
8BitDo Ultimate Wireless / Pro 2 Wired Controller
  USB ID: 2dc8:3106
  型号: 8BitDo Ultimate 2.4G Controller

Generic X-Box pad
  USB ID: 2dc8:200f
  型号: 8BitDo Ultimate 3-mode Controller for Xbox
```

两者现已加入自动检测白名单。默认运行：

```bash
ros2 run my_joystick_driver joystick_node
```

会自动连接当前插入的任一手柄。原有 `device_name_filter` 继续有效，可用于临时匹配其他 evdev 手柄名称。ABXY、摇杆和方向键映射本次不变。

新 3-mode Xbox 手柄的 L2/R2 原始范围为 `0..1023`，旧 2.4G 手柄为 `0..255`。本次按要求只修正自动检测；如果使用新手柄扳机控制机构，仍需后续将轴范围改为从 evdev `AbsInfo` 动态读取。

## 2026-06-16 8BitDo P1／P2 背鍵狀態

`evtest` 實測：同一個手柄 event 裝置中 A/B/X/Y 有輸出，但 P1／P2 沒有獨立輸出。因此目前
driver 不新增 `p1`／`p2` 映射，`my_joystick_msgs/msg/Joystick.msg` 也不新增欄位。

目前採用 8BitDo 軟體內部 remap：

```text
P1 = R3
P2 = L3
```

driver 仍按既有 mapping 發布：

```text
P1 -> r3: true
P2 -> l3: true
```

這是手柄韌體層替代按鍵，不是 ROS 獨立按鍵。若未來某個連線模式下 P1／P2 能產生獨立
`EV_KEY` code，再擴充 `button_mapping` 與 `Joystick.msg`。


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 P1/P2 現行用途

P1/P2 仍不作為獨立 ROS message 欄位。手柄內部 remap 維持：`P1=R3`，`P2=L3`。目前實際用途只在 STAFF mode 生效：`P1/R3 -> Motor7 inclination/head relay`，`P2/L3 -> Motor8 inclination/head relay`。

若未來更換連線模式後 P1/P2 能輸出獨立 evdev key code，才需要擴充 `Joystick.msg` 與 `joystick_node.py`。

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
