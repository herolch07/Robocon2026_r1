> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# R1 Chassis Speed Tuning Notes

本文记录 R1 底盘速度相关参数、计算方式和实机调参注意事项。

## 1. 主要速度参数

### joystick_bridge

```text
max_speed_cm
```

含义：底盘目标最大平移速度，单位 `cm/s`。

例如：

```bash
ros2 param set /joystick_bridge max_speed_cm 400.0
```

表示左摇杆推到底时，`joystick_bridge` 会尝试发布约 `400 cm/s` 的底盘平移目标速度。

```text
max_rotation
```

含义：底盘目标最大旋转角速度，单位 `rad/s`。

例如：

```bash
ros2 param set /joystick_bridge max_rotation 1.0
```

表示右摇杆推到底时，目标旋转角速度约为 `1 rad/s`。

### local_navigation_node

```text
max_wheel_speed_rad_s
```

含义：单个轮子的最大角速度限制，单位 `rad/s`。

如果 `joystick_bridge` 要求的底盘速度换算后超过这个轮速限制，`local_navigation_node` 会按比例缩放四个轮子的速度。

```text
max_wheel_accel_rad_s2
```

含义：单个轮子的角加速度限制，单位 `rad/s^2`。

它限制轮速变化得有多快。数值越小，起步和刹车越柔和；数值越大，响应越快但电流冲击越大。

## 2. 当前默认值

| 参数 | 默认值 | 单位 | 所属节点 | 作用 |
|---|---:|---|---|---|
| `max_speed_cm` | `150.0` | `cm/s` | `/joystick_bridge` | 左摇杆推到底时的目标最大平移速度 |
| `max_rotation` | `3.0` | `rad/s` | `/joystick_bridge` | 右摇杆推到底时的目标最大旋转角速度 |
| `translation_linear_weight` | `0.1` | ratio | `/joystick_bridge` | 平移混合曲线线性权重 |
| `rotation_linear_weight` | `0.1` | ratio | `/joystick_bridge` | 旋转混合曲线线性权重 |
| `deadzone` | `15` | joystick units | `/joystick_bridge` | 摇杆小幅漂移过滤，当前摇杆范围是 `-512..512` |
| `input_timeout_sec` | `0.3` | `s` | `/joystick_bridge` | `/joystick_data` 超时后发布底盘停止指令 |
| `max_wheel_speed_rad_s` | `40.0` | `rad/s` | `/local_navigation_node` | 单个轮子的角速度上限 |
| `max_wheel_accel_rad_s2` | `25.0` | `rad/s^2` | `/local_navigation_node` | 单个轮子的角加速度上限 |
| `omniwheel_radius_m` | `0.0635` | `m` | `/local_navigation_node` | 全向轮半径，用于线速度/角速度换算 |
| `command_timeout_sec` | `0.3` | `s` | `/local_navigation_node` | `/local_driving` 超时后 Motor 1-4 归零 |
| `command_timeout_sec` | `0.5` | `s` | `/motor_controller_node` | 连续 VEL 命令超时后对应电机归零 |

源码当前默认值摘要：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
max_rotation = 3.0
rotation_linear_weight = 0.1
Motor7/8 position_b_rad = 32.0
Motor7/8 position_c_rad = -32.0
Motor7/8 preset_speed_rad_s = 3.0
Motor7/8 trim_speed_rad_s = 2.0
deadzone = 15
input_timeout_sec = 0.3
max_wheel_speed_rad_s = 40.0
max_wheel_accel_rad_s2 = 25.0
omniwheel_radius_m = 0.0635
local_navigation_node command_timeout_sec = 0.3
damiao_node command_timeout_sec = 0.5
```

默认值偏保守，适合低速联调。

## 3. 如何查看和设置

查看当前参数：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge max_rotation
ros2 param get /joystick_bridge deadzone
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node max_wheel_speed_rad_s
ros2 param get /local_navigation_node max_wheel_accel_rad_s2
ros2 param get /local_navigation_node omniwheel_radius_m
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
```

低速安全测试：

```bash
ros2 param set /joystick_bridge max_speed_cm 40.0
ros2 param set /joystick_bridge max_rotation 0.6
ros2 param set /local_navigation_node max_wheel_speed_rad_s 8.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 8.0
```

中速测试：

```bash
ros2 param set /joystick_bridge max_speed_cm 60.0
ros2 param set /joystick_bridge max_rotation 0.8
ros2 param set /local_navigation_node max_wheel_speed_rad_s 12.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 12.0
```

较高速测试：

```bash
ros2 param set /joystick_bridge max_speed_cm 100.0
ros2 param set /joystick_bridge max_rotation 1.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 20.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 15.0
```

理论接近 `400 cm/s` 的高风险设置：

```bash
ros2 param set /joystick_bridge max_speed_cm 400.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 64.0
```

这些 `ros2 param set` 是运行时临时设置。重启对应节点或重新运行 `./r1_start_base_1_0.sh` 后，会回到源码默认值，除非你把参数写入 launch/YAML 或源码默认值。

## 4. 速度计算

底盘纯平移速度和轮子角速度的理想关系：

```text
chassis_speed_m_s = wheel_speed_rad_s * wheel_radius_m
```

当前 source 默认：

```text
wheel_radius_m = 0.0635
max_wheel_speed_rad_s = 40.0
```

理论轮子线速度：

```text
40.0 * 0.0635 = 2.540 m/s = 254.0 cm/s
```

所以当前 `150 cm/s` 手柄目标在纯前后/左右平移时不会被 `40 rad/s` 轮速限制截断；斜向或叠加满旋转时仍可能触发四轮同比缩放。

旧的 `64 rad/s / 400 cm/s` 段落属于历史高风险测试记录：

```text
64.0 * 0.0635 = 4.064 m/s = 406.4 cm/s
```

这高于 DM-S3519 输出轴实际能力边界，不应作为当前默认设置。

## 5. 加速度计算

线加速度和轮子角加速度的理想关系：

```text
chassis_accel_m_s2 = wheel_accel_rad_s2 * wheel_radius_m
```

当前 source 默认：

```text
max_wheel_accel_rad_s2 = 25.0
wheel_radius_m = 0.0635
```

理论线加速度约为：

```text
25.0 * 0.0635 = 1.5875 m/s^2
```

纯前后/左右平移到 `150 cm/s` 约需要：

```text
1.5 / 1.5875 = 0.94 s
```

到 `40 rad/s` 轮速对应的 `254 cm/s` 理论边界约需要：

```text
2.54 / 1.5875 = 1.60 s
```

这些是理想计算；真实加速仍受电机、驱动器限流、电池、轮子抓地力、载重和地面影响。

## 6. 22.8V 和 20kg 载重的影响

重量不会直接进入这个理想公式：

```text
speed = wheel_rad_s * wheel_radius
```

所以从几何关系上看，理论最高速度主要由以下因素决定：

```text
电机最高转速
轮子半径
减速比
电压下的可达转速
```

但是 20kg 载重会明显影响真实表现：

```text
能不能加速到目标速度
达到目标速度需要多久
高速时能不能维持
急加速/急停是否过流
轮子是否打滑
电池电压是否下跌
电机和驱动器是否发热或保护
```

22.8V 说明电压不低，但仍不能单独证明底盘能稳定跑到 `400 cm/s`。还需要确认电机扭矩、驱动器限流、电池放电能力、减速比、地面摩擦和机械结构。

## 7. Warning Points

### 不要直接跳到高速

不要在未知硬件状态下直接使用：

```bash
ros2 param set /joystick_bridge max_speed_cm 400.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 64.0
```

原因：

```text
400 cm/s = 4.0 m/s
20kg 载重下起步、急停、横移、旋转都会产生很大电流和机械冲击
```

### 重载时优先控制加速度

20kg 载重下，真正危险的往往不是目标最高速度，而是加速度太大：

```text
max_wheel_accel_rad_s2 太高
-> 起步/急停很猛
-> 电流冲击大
-> 轮子可能打滑
-> 驱动器可能保护
-> CAN/USB-CAN 可能断连
```

重载初测建议：

```text
max_wheel_accel_rad_s2 = 6.0 .. 12.0
```

### 如果出现这些现象，立即降速

```text
驱动器红灯或保护
CAN/USB-CAN 断连
电机或驱动器明显发热
底盘横移时抖动或顶轮
轮子明显打滑
电池电压明显下跌
机器人急停时结构晃动很大
```

优先降低：

```bash
ros2 param set /joystick_bridge max_speed_cm 40.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 8.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 6.0
```

### 速度单位不要混淆

```text
cm/s     = chassis 平移目标速度
rad/s    = 轮子角速度或底盘旋转角速度
rad/s^2  = 轮子角加速度
```

`max_speed_cm` 不是实测速度，它只是 `joystick_bridge` 发出的目标速度。真实速度可能因为限流、打滑、载重、电池电压、地面和电机能力而低于目标值。

## 8. 推荐调参顺序

不要直接从低速跳到 `400 cm/s`。建议逐级测试：

```bash
ros2 param set /joystick_bridge max_speed_cm 40.0
ros2 param set /joystick_bridge max_rotation 0.6
ros2 param set /local_navigation_node max_wheel_speed_rad_s 8.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 8.0
```

稳定后：

```bash
ros2 param set /joystick_bridge max_speed_cm 60.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 12.0
ros2 param set /local_navigation_node max_wheel_accel_rad_s2 12.0
```

再逐步测试：

```text
100 cm/s
150 cm/s
200 cm/s
```

只有确认电流、温度、抓地力和结构都稳定后，才考虑更高速度。

## 9. 高速设置示例

理论上接近 `400 cm/s` 的设置：

```bash
ros2 param set /joystick_bridge max_speed_cm 400.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 64.0
```

这是旧高风险测试示例；当前默认 `max_wheel_accel_rad_s2=25.0`，且当前默认轮速上限为 `40.0 rad/s`。

不建议在 20kg 载重实机上直接使用这个设置。应先低速逐步测试。

## 10. 查看当前参数

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge max_rotation
ros2 param get /local_navigation_node max_wheel_speed_rad_s
ros2 param get /local_navigation_node max_wheel_accel_rad_s2
ros2 param get /local_navigation_node omniwheel_radius_m
```

## Domain isolation before speed testing

Before any speed test, confirm R1 is not seeing R2 topics:

```bash
echo $ROS_DOMAIN_ID
echo $ROS_LOCALHOST_ONLY
ros2 topic list
```

R1 speed tests must not be run while `/base/dummy_control` or `/damiao_motor_controller` from R2 is visible. Current controller speed levels have been removed; source default is `max_speed_cm=150.0 cm/s`.

## 2026-06-06 当前平移控制策略

当前默认平移上限为 `150 cm/s`、旋转上限为 `3.0 rad/s`、Motor 7/8 STAFF 位置模式按各自 controller 参数运行；三者均采用 `y = 0.1x + 0.9x³`。START/SELECT 底盘速度档已取消。本文较早章节中的调速命令属于历史调试记录。

## 2026-06-10 当前有效速度边界（取代旧 64 rad/s / 400 cm/s 方案）

本节是当前 DM-S3519 底盘的有效配置。本文前面的 `64 rad/s`、`400 cm/s` 内容属于历史调试记录，不应作为当前实机参数。

### 当前参数

```text
joystick_bridge.max_speed_cm = 150.0 cm/s
joystick_bridge.max_rotation = 3.0 rad/s
local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s
local_navigation_node.max_wheel_accel_rad_s2 = 25.0 rad/s^2
omniwheel_radius_m = 0.0635 m
wheel_base_radius_m = 0.327038 m
```

### 三层速度限制

1. `joystick_bridge.max_speed_cm` 决定左摇杆满杆发布的目标平移速度。
2. `local_navigation_node.max_wheel_speed_rad_s` 限制任意单轮速度；一个轮子超限时，四轮同比缩放。
3. DM-S3519 的实际转速、负载、电池电压、地面抓地力和驱动器保护决定真实可达到速度。

因此，提高 `max_speed_cm` 只会提高目标值，不能绕过 `40 rad/s` 轮速限制或电机机械能力。

### 基本换算

```text
轮缘速度 = 轮子角速度 × 轮半径
纯前后/左右所需轮速 = 底盘速度 / 轮半径
当前校准矩阵斜向最坏轮速 = 底盘速度 × sqrt(2) / 轮半径
旋转叠加轮速 = rotation_rad_s × wheel_base_radius_m / wheel_radius_m
```

满旋转 `3.0 rad/s` 对单轮增加约：

```text
3.0 × 0.327038 / 0.0635 = 15.45 rad/s
```

### 当前软件和电机理论上限

| 边界 | 轮速 | 纯前后/左右 | 斜向最坏方向 |
|---|---:|---:|---:|
| 当前手柄默认目标 | - | `150 cm/s` | `150 cm/s` |
| 当前软件轮速限制 | `40.00 rad/s` | `254 cm/s` | `180 cm/s` |
| DM-S3519 额定 395 rpm | `41.36 rad/s` | `263 cm/s` | `186 cm/s` |
| DM-S3519 空载最高 435 rpm | `45.55 rad/s` | `289 cm/s` | `205 cm/s` |

这些是几何理论值，不是带载实测速度。斜向值较低，是因为当前 forward/lateral 校准矩阵在 45 度方向会让最忙的单轮承担约 `sqrt(2)` 倍平移分量。

### 150 cm/s 当前状态

```text
纯前后/左右：1.50 / 0.0635 = 23.62 rad/s
斜向最坏方向：23.62 × sqrt(2) = 33.41 rad/s
斜向 + 3.0 rad/s 满旋转：33.41 + 15.45 = 48.86 rad/s
```

因此当前 `150 cm/s` 纯平移不会被 `40 rad/s` 截断；但斜向同时叠加满旋转会触发四轮同比缩放。纯前后/左右 + 满旋转约为 `23.62 + 15.45 = 39.07 rad/s`，仍低于 `40 rad/s`。

### 如何提高到 170 cm/s

临时运行时设置：

```bash
ros2 param set /joystick_bridge max_speed_cm 170.0
```

查看是否生效：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /local_navigation_node max_wheel_speed_rad_s
```

`170 cm/s` 的计算：

```text
纯前后/左右：1.70 / 0.0635 = 26.77 rad/s
斜向最坏方向：26.77 × sqrt(2) = 37.86 rad/s
斜向 + 满旋转：37.86 + 6.18 = 44.04 rad/s
```

所以 `170 cm/s` 纯平移可以运行；斜向再叠加最大旋转时会超过 `40 rad/s`，`local_navigation_node` 会同比缩放四轮，实际平移和旋转都低于目标值。

若要永久改为 `170 cm/s`，修改 `joystick_bridge.py` 中 `max_speed_cm` 的默认值，或后续写入 YAML/launch。仅运行 `ros2 param set` 会在节点重启后恢复 `150 cm/s`。

### 为什么当前保持 40 rad/s

- DM-S3519 额定输出轴速度约 `41.36 rad/s`，`40 rad/s` 留有少量额定余量。
- 旧 `64 rad/s` 相当于约 `611 rpm`，高于电机 `435 rpm` 空载最高规格。
- 限制组合动作的单轮峰值，可降低过流、母线压降、回生过压、打滑和 CAN/驱动器保护风险。
- 四轮同比缩放可保留运动方向比例，不会只截断某一轮导致运动方向明显改变。

### VMAX=200 不代表机械速度 200 rad/s

`PMAX/VMAX/TMAX` 是 CAN 定点反馈的映射范围。若实机为：

```text
PMAX = 12.5
VMAX = 200
TMAX = 10
```

`VMAX=200` 只用于把 12-bit 反馈速度还原成 `rad/s`，不表示 DM-S3519 输出轴能够达到 `200 rad/s`。VEL 模式发送的是浮点 `rad/s`，机械速度仍受额定 `395 rpm`、空载最高 `435 rpm` 和驱动器 `MAX_SPD` 限制。

### 调高速度的推荐步骤

```text
150 -> 160 -> 170 cm/s
```

每一级在实际载重和比赛地面测试：纯前进、纯横移、斜向、原地旋转、斜向加旋转、满速松杆和正反快速切换。监控 `/damiao_motor_status`、电池压降、驱动器故障码、MOS/转子温度和轮胎打滑。当前不建议在保持 `40 rad/s` 轮速限制时直接把手柄目标改到 `200 cm/s` 以上。

## 2026-06-11 加速度限制模式说明（source-verified current）

当前 `max_wheel_accel_rad_s2 = 25.0` 保持不变。`local_navigation_node` 目前支持两种模式：

```text
accel_limit_mode = per_wheel   # 默认，直接启动 start base 时使用
accel_limit_mode = vector      # 可手动切换，四轮共享同一个 alpha
```

默认 `per_wheel` 会对每个轮子的速度变化分别做 `±max_delta` 限制，手感更直接。可选 `vector` 模式才会使用四轮统一比例：

```text
alpha = min(1, 25 * dt / max(abs(target_wheel_i - current_wheel_i)))
new_wheel_i = current_wheel_i + alpha * (target_wheel_i - current_wheel_i)
```

因此，当前直接启动不会启用 vector limit。需要临时测试时才执行：

```bash
ros2 param set /local_navigation_node accel_limit_mode vector
```

这类加速度限制只影响加速和方向切换阶段，不是 IMU 航向闭环。如果底盘达到稳定速度后仍持续转向，应检查轮子接地、滚子阻力、载重分布和四轮实际输出差异。

## 2026-06-20 当前旋转速度更新

当前右摇杆满杆旋转速度为：

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

这不会改变 `max_speed_cm = 150 cm/s` 和 `local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s`。但它会改变组合动作边界：

```text
纯前后/左右 150 cm/s + 满旋转 3.0 rad/s: 23.62 + 15.45 = 39.07 rad/s
斜向最坏 150 cm/s + 满旋转 3.0 rad/s: 33.41 + 15.45 = 48.86 rad/s
```

所以纯平移不会触发 `40 rad/s` 轮速限制；纯前后/左右加满旋转已经非常接近上限；斜向加满旋转会被 `local_navigation_node` 四轮同比速度限幅缩放。

## 2026-06-20 Current Rotation Default

Current source default:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

Older sections mentioning `1.2 rad/s` or `2.4 rad/s` are historical and are not the current runtime default.

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
