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
| `max_speed_cm` | `20.0` | `cm/s` | `/joystick_bridge` | 左摇杆推到底时的目标最大平移速度 |
| `max_rotation` | `0.5` | `rad/s` | `/joystick_bridge` | 右摇杆推到底时的目标最大旋转角速度 |
| `deadzone` | `24` | joystick units | `/joystick_bridge` | 摇杆小幅漂移过滤，当前摇杆范围是 `-512..512` |
| `input_timeout_sec` | `0.3` | `s` | `/joystick_bridge` | `/joystick_data` 超时后发布底盘停止指令 |
| `max_wheel_speed_rad_s` | `64.0` | `rad/s` | `/local_navigation_node` | 单个轮子的角速度上限 |
| `max_wheel_accel_rad_s2` | `12.0` | `rad/s^2` | `/local_navigation_node` | 单个轮子的角加速度上限 |
| `omniwheel_radius_m` | `0.0635` | `m` | `/local_navigation_node` | 全向轮半径，用于线速度/角速度换算 |
| `command_timeout_sec` | `0.3` | `s` | `/local_navigation_node` | `/local_driving` 超时后 Motor 1-4 归零 |
| `command_timeout_sec` | `0.5` | `s` | `/motor_controller_node` | 连续 VEL 命令超时后对应电机归零 |

源码当前默认值摘要：

```text
max_speed_cm = 20.0
max_rotation = 0.5
deadzone = 24
input_timeout_sec = 0.3
max_wheel_speed_rad_s = 64.0
max_wheel_accel_rad_s2 = 12.0
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

当前轮半径：

```text
wheel_radius_m = 0.0635
```

如果设置：

```text
max_wheel_speed_rad_s = 64.0
```

理论轮子线速度：

```text
64.0 * 0.0635 = 4.064 m/s
```

换算：

```text
4.064 m/s = 406.4 cm/s
```

因此，如果同时设置：

```bash
ros2 param set /joystick_bridge max_speed_cm 400.0
ros2 param set /local_navigation_node max_wheel_speed_rad_s 64.0
```

理论纯平移最高目标速度约为：

```text
min(400.0, 406.4) = 400.0 cm/s
```

也就是：

```text
400 cm/s = 4.0 m/s
```

## 5. 加速度计算

线加速度和轮子角加速度的理想关系：

```text
chassis_accel_m_s2 = wheel_accel_rad_s2 * wheel_radius_m
```

默认：

```text
max_wheel_accel_rad_s2 = 12.0
```

线加速度约为：

```text
12.0 * 0.0635 = 0.762 m/s^2
```

从 `0` 加速到 `4.0 m/s`，理论需要：

```text
4.0 / 0.762 = 5.25 s
```

速度随时间大约为：

```text
1 s: 76 cm/s
2 s: 152 cm/s
3 s: 229 cm/s
4 s: 305 cm/s
5 s: 381 cm/s
5.25 s: 400 cm/s
```

前提是电机、驱动器、电池和轮子抓地力都能支持。

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

如果 `max_wheel_accel_rad_s2` 保持默认 `12.0`，加速到目标速度大约需要 `5.25 s`。

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

R1 speed tests must not be run while `/base/dummy_control` or `/damiao_motor_controller` from R2 is visible. Current controller speed levels are `10/20/40/60/100/150 cm/s`.

## 2026-06-06 当前平移控制策略

当前默认 `max_speed_cm = 150.0`，左摇杆采用 `y = 0.2x + 0.8x³`。START/SELECT 速度档已取消。本文较早章节中的 20/40/60/100/400 cm/s 手动调速命令属于历史调试记录。
