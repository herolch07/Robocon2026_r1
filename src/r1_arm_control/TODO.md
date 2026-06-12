# r1_arm_control TODO

## 已完成

- [x] 建立 `r1_arm_control` package
- [x] 实现升降电机 controller，默认 Motor 5
- [x] 实现水平移动电机 controller，默认 Motor 6
- [x] 实现夹爪电机 controller，默认 Motor 7
- [x] 实现 L2/R2 控制升降
- [x] 实现 D-pad 控制水平移动和速度档位
- [x] 实现 L1/R1 控制夹爪
- [x] Motor 7 支持 0.5s 两段式速度及 START/SELECT 高速档调节
- [x] 三个 controller 均实现 `timeout_sec` 安全归零
- [x] 新增 README，记录 topic、参数、timeout 行为和启动方式

## 待完成

- [ ] 将三个 controller 的重复安全逻辑抽成 package 内部 helper，减少重复代码
- [ ] 为 controller 增加 launch 文件和 YAML 参数文件
- [ ] 为 joystick bridge 增加可配置按键映射
- [ ] 增加无硬件 topic 级测试
- [ ] 根据真实机械限位加入软限位或 limit switch 输入

## 2026-06-07 升降与夹爪按键交换

- [x] Motor 5 升降改为 R1/L1 固定速度控制
- [x] Motor 7 机械夹爪改为 R2/L2 模拟调速
- [x] 移除 Motor 7 旧两段式速度逻辑
- [x] 移除 Motor 7 START/SELECT 高速档调节
- [x] 保持 Motor 5/7 controller timeout 与 Motor ID 不变
- [ ] 离地确认 Motor 5 与 Motor 7 正反方向
- [ ] 实机确认 Motor 7 扳机低速控制手感

## 2026-06-07 Motor 7 混合曲线

- [x] 新增 `gripper_linear_weight = 0.1`
- [x] R2/L2 净输入使用 `y = 0.1x + 0.9x³`
- [x] 保持 `max_speed_rad_s = 1.3` 与 `trigger_deadzone = 24` 不变
- [x] 保持 controller `timeout_sec = 0.3 s` 安全归零
- [ ] 实机确认小扳机输入足以克服夹爪机械摩擦
- [ ] 实机确认满按 R2/L2 的正反方向与最高速度


## 2026-06-12 Motor 8 POS_VEL 实验

- [x] 保持 Motor 7 原有 R2/L2 速度控制不变
- [x] 新增 `motor8_position_joystick_bridge_node`
- [x] X 上升沿在两个预设位置之间切换
- [x] L3/R3 提供不占用 Motor 7 扳机的正反微调
- [x] 新增 `motor8_position_controller_node`
- [x] 预设位置、速度、软限位和按键全部参数化
- [x] 手柄超时后停止移动目标并保持实时位置
- [x] 反馈丢失、急停恢复时不重放旧目标位置
- [x] 新增双位置、按键边沿和软限位无硬件测试
- [ ] 离地确认 Motor 8 正负方向
- [ ] 实测确定 `position_a_rad` 和 `position_b_rad`
- [ ] 实测确定安全软限位，替换当前 `-0.5..0.5 rad` 试验值
- [ ] 确认 `0.3 rad/s` 自动速度和 `0.1 rad/s` 微调速度是否合适
- [ ] Motor 8 实验通过后，再评估是否将 Motor 7 改为相同模式

## 2026-06-13 Motor 8 多圈初测参数

- [x] 将 `position_b_rad = 33.0 rad` 固化为源码默认值
- [x] 将软限位固化为 `-35.0..35.0 rad`
- [x] 将 X 自动定位速度固化为 `3.0 rad/s`
- [x] 将 L3/R3 微调速度固化为 `2.0 rad/s`
- [ ] 明日复测 X 在 `0.0 <-> 33.0 rad` 间往返是否稳定
- [ ] 复测 `actual_q` 超过 `+-12.5 rad` 后是否饱和
- [ ] 复测手柄断连时多圈位置保持是否正确
- [ ] 复测急停恢复后不会重放旧的 `33 rad` 目标
- [ ] 完成 Motor 8 验证后，再决定是否迁移 Motor 7
