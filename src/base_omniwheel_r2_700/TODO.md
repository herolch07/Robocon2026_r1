# base_omniwheel_r2_700 TODO

## 已完成

- [x] 实现 `local_navigation_node` 四轮全向底盘逆运动学
- [x] 实现 `damiao_node` 达妙电机 VEL 模式控制
- [x] 支持 Motor 1-7 初始化
- [x] 修复轮径换算，使用 `63.5 mm` 全向轮半径
- [x] 增加 `local_navigation_node` 输入 timeout，`/local_driving` 中断后 Motor 1-4 归零
- [x] 增加 `damiao_node` 电机级 watchdog，连续 VEL 命令超时后对应电机归零
- [x] README 追加 2026-05-14 安全更新说明
- [x] 修正 `local_navigation_node` 横向平移符号，避免左/右平移变成原地旋转
- [x] 将 `local_navigation_node` 的轮距、轮径、横向符号、旋转符号、电机方向改为 ROS 参数
- [x] 将 `local_navigation_node` 的 forward/lateral/rotation 运动基底改为可校准参数
- [x] 早期实机测试曾将 `lateral_axis_sign` 默认值校准为 `-1.0`；最终实机确认已在 2026-05-22 改为 `1.0`
- [x] 增加 `max_wheel_speed_rad_s` 轮速限幅，降低斜向/叠加动作导致驱动器过流风险
- [x] 增加 `max_wheel_accel_rad_s2` 加速度限制，降低摇杆突变导致 CAN/驱动器断连风险

## 待完成

- [ ] 将 `damiao_node` 拆分到独立 `damiao_driver` package，避免底盘 package 承担全机器人电机 driver 职责
- [ ] 将 `local_navigation_node` 参数整理到 YAML/launch 文件
- [ ] 将 `damiao_node` motor_id 映射改成 YAML/launch 参数
- [ ] 为 `local_navigation_node` 增加自动化测试
- [ ] 为 `damiao_node` 增加无硬件 mock 测试
- [ ] 整理旧 VESC 节点，确认是否仍属于当前 R1/R2 工程范围
- [ ] 实机重新校准斜向运动基底，确认右下、右上、左下、左上四个方向均无互相顶轮

## 2026-05-22 横向平移修复

- [x] 确认实机轮位为 Motor 1 左前、Motor 2 右前、Motor 3 右后、Motor 4 左后
- [x] 将 `local_navigation_node` 默认 `lateral_coeff_1..4` 修正为 `[1, -1, -1, 1]`
- [x] README 追加 v6 横向平移轮速基底修正说明
- [x] 实机测试左摇杆左推左横移、右推右横移
- [x] 根据实机反馈将 `lateral_axis_sign` 最终默认值记录为 `1.0`
- [ ] 重新测试斜向移动，确认前左/前右/后左/后右四个斜向无明显顶轮

## 2026-05-22 左右方向与右摇杆旋转修复

- [x] 根据实机反馈将 `lateral_axis_sign` 默认值改为 `1.0`
- [x] 曾尝试将 `rotation_coeff_1..4` 改为 `[1, 1, 1, 1]`，实机结果为四轮转动但车体不旋转
- [x] README 追加 v7 左右方向与右摇杆原地旋转修正说明
- [x] 实机确认左摇杆左/右方向正确
- [ ] 重新实机确认右摇杆左/右为原地旋转，没有明显平移
- [x] 当前 `rotation_axis_sign = 1.0` 可用，暂不需要反向

## 2026-05-22 最终实机确认

- [x] Controller 启动完整系统后，底盘前后、左右横移、原地旋转均工作成功
- [x] Motor 5 elevator 可由 L2/R2 控制
- [x] Motor 6 horizontal 可由 D-pad 左/右控制
- [x] Motor 7 arm gripper 可由 L1/R1 控制
- [x] Arduino pneumatic gripper 可由 A/B/X 控制
- [x] README 已追加 v8 最终实机确认版
- [ ] 后续将最终参数整理到 YAML/launch 文件，避免只依赖源码默认值

## 2026-05-22 右摇杆旋转复修

- [x] 根据实机反馈确认 `[1, 1, 1, 1]` rotation 基底不能产生原地旋转
- [x] 将 `rotation_coeff_1..4` 最终确认并固化为 `[1, -1, 1, -1]`
- [x] README 追加 v9 右摇杆旋转基底复修说明
- [x] 实机复测确认右摇杆左/右可原地旋转
- [ ] 如旋转方向相反，通过 `rotation_axis_sign` 校准并记录最终值

## 2026-05-25 400 cm/s 速度上限准备

- [x] 将 `max_wheel_speed_rad_s` 默认值改为 `64.0`，理论覆盖约 `406 cm/s` 轮子线速度
- [x] README 追加 v10 速度上限说明
- [ ] 实机逐级测试 10/20/40/60/100/150 cm/s 档位稳定性
- [ ] 根据实机电流、温度、打滑情况决定是否提高或降低 `max_wheel_accel_rad_s2`

## 2026-05-27 200 cm/s 保护问题

- [x] 记录 `200 cm/s` 档位导致底盘突然断反应的问题
- [x] 曾临时将 controller 默认最高档改为 `150 cm/s`
- [x] 按用户要求保持 `max_wheel_speed_rad_s = 64.0 rad/s` 不变
- [ ] 检查 200 cm/s 时电池电压是否瞬间下跌
- [ ] 检查 DM 驱动器状态灯/保护码
- [ ] 检查 CAN 是否断连或 damiao_node 是否报错

## 2026-05-27 恢复速度档位复测

- [x] 曾按用户要求恢复 joystick_bridge 默认速度档位到 10/20/60/100/200/400 cm/s 用于对比测试
- [x] 保持 `max_wheel_speed_rad_s = 64.0 rad/s` 不变
- [ ] 复测更换 board 后持续 hold 左摇杆的问题

## 2026-05-28 ROS domain 隔离确认

- [x] 确认 R1 曾经看到 R2 的 `/damiao_motor_controller`、`/base/dummy_control` 等 node/topic
- [x] R1 启动脚本固定 `ROS_DOMAIN_ID=1`、`ROS_LOCALHOST_ONLY=1`
- [x] controller 默认最高档设置为 `150 cm/s` 路线
- [ ] 隔离环境下复测底盘持续 hold 左摇杆稳定性

## 2026-06-07 急停断电自动恢复

- [x] 为 Motor 1-7 记录最后反馈时间和 `isEnable`
- [x] 反馈超时或失能时进入 `RECOVERING`
- [x] 恢复期间只发送 `0 rad/s`，阻止非零命令
- [x] 每 `2.0 s` 自动发送 `VEL mode + enable + zero`
- [x] 收到已使能反馈后进入 `WAIT_NEUTRAL`
- [x] 要求手柄/上游回中一次后才进入 `READY`
- [x] USB-CAN 串口改为低频无限重连
- [x] 新增 `/damiao_motor_status` 恢复状态 topic
- [x] 增加无硬件恢复状态机测试
- [x] 实机架空测试急停按下超过 10 秒后自动恢复
- [x] 实机确认急停释放时保持摇杆非零不会立即驱动电机


## 2026-06-10 USB-CAN 串口权限

- [x] 确认 `/dev/ttyACM0` 属于 `root:dialout` 且当前用户缺少 `dialout` 组权限
- [x] `damiao_node` 在 `Errno 13` 时输出永久权限修复命令
- [x] README 追加 `dialout` 配置、重新登录与验证步骤
- [ ] 将部署用户加入 `dialout` 组后重新登录并完成 USB-CAN 实机连接验证

## 2026-06-10 DM-S3519 反馈与速度边界修正

- [x] 按 DM-S3519-1EC 手册确认 VEL 指令和反馈速度均为减速器输出轴 `rad/s`
- [x] 修复 USB-CAN `16 byte` 接收帧边界和半帧缓存
- [x] 按 `DATA[0]` 低/高 4 bit 分别解析电机 ID 与状态码
- [x] 按协议字段解析位置、速度、转矩、MOS 温度和转子温度
- [x] 将电机枚举由 `DMH3510` 修正为 `DMS3519`
- [x] 将默认轮速上限由历史 `64.0 rad/s` 修正为 `40.0 rad/s`
- [x] 新增 DM-S3519 反馈帧单元测试
- [x] README 追加 v13 协议、单位、限幅和超时行为说明
- [ ] 读取 7 台实机的 `PMAX/VMAX/TMAX` 寄存器并替换临时映射值
- [ ] 架空逐台验证反馈 ID、速度方向、状态码和温度
- [ ] 实机验证 150 cm/s 纯平移及平移/旋转叠加时是否触发 `40.0 rad/s` 同比限幅

## 2026-06-10 当前理论速度文档

- [x] 记录当前 `150 cm/s` 手柄目标和 `40 rad/s` 软件轮速限制
- [x] 记录 DM-S3519 额定 395 rpm 与空载最高 435 rpm 的理论底盘速度
- [x] 区分纯前后/左右与斜向最坏方向速度边界
- [x] 记录 150/170 cm/s 在平移和旋转叠加时的单轮需求
- [x] 记录临时调参、永久修改方式和逐级提速测试步骤
- [x] 说明 `VMAX=200` 是反馈映射范围，不是电机机械速度
- [ ] 实机带载测量 150/160/170 cm/s 的实际速度、电流、压降和温度

## 2026-06-11 四轮统一矢量加速度限制

- [x] 删除四轮逐个独立截断的加速度限制实现
- [x] 使用统一 `alpha` 缩放整组四轮速度变化
- [x] 保持 `max_wheel_accel_rad_s2 = 25.0 rad/s^2`
- [x] 保持 `max_wheel_speed_rad_s = 40.0 rad/s` 四轮同比限幅
- [x] 新增 22° 类不等轮速比例保持测试
- [x] 新增最大轮速变化量和直通行为测试
- [x] README 追加 v15 原因、算法、影响边界和实机步骤
- [ ] 实机测试 0°/22°/45°/90° 起步与方向切换偏航
- [ ] 记录偏航发生在加速阶段还是匀速阶段
- [ ] 若匀速仍偏航，检查轮组接地并校准四轮输出增益


## 2026-06-12 Motor 8 POS_VEL 支持

- [x] 默认电机列表增加 Motor 8
- [x] 新增 `position_mode_motor_ids = [8]` 混合模式参数
- [x] Motor 1-7 保持 VEL，Motor 8 初始化和恢复使用 POS_VEL
- [x] POS_VEL 恢复时保持实时位置，不重放旧目标
- [x] 增加位置命令 watchdog
- [x] `/damiao_motor_status` 追加 q/dq/tau/control_mode
- [x] 新增 Motor 8 混合模式与急停恢复无硬件测试
- [ ] 实机确认 Motor 8 CAN ID 为 8 且反馈正确归属
- [ ] 后续按 chassis/mechanism 拆分两个 USB-CAN driver 实例和稳定设备路径

## 2026-06-13 Motor 7 加入 POS_VEL

- [x] 默认 `position_mode_motor_ids` 改为 `[7, 8]`
- [x] Motor 7/8 共用位置模式恢复与安全保持逻辑
- [x] 保持 Motor 1-6 的 VEL 控制不变
- [ ] 实机确认 Motor 7 的 POS_VEL 反馈与急停恢复
