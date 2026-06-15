# Joystick Bridge 开发任务清单

## v1.0.0 基础功能（已完成）
- [x] 创建 ROS2 Python 包结构
- [x] 实现基本的消息订阅和发布
- [x] 完成摇杆到导航指令的映射逻辑
- [x] 添加死区过滤功能
- [x] 编写完整的 README 文档
- [x] 符合 AGENTS.md 工程规范
- [x] 增加 `/joystick_data` 输入 watchdog，超时后发布 `/local_driving = [0,0,0]`
- [x] README 追加 2026-05-14 watchdog 说明
- [x] 将右摇杆默认最大旋转速度 `max_rotation` 从 `2.0 rad/s` 先降到 `1.0 rad/s`
- [x] 为降低实机联调风险，将默认 `max_speed_cm` 调整为 `20.0 cm/s`，`max_rotation` 调整为 `0.5 rad/s`

## 待完善功能
- [x] 添加 START/SELECT 按键映射支持，用于底盘速度档位切换
- [x] 实现 START/SELECT 速度档位切换（10/20/40/60/100/150 cm/s）
- [ ] 添加紧急停止功能映射
- [ ] 支持多手柄输入（预留扩展）

## 性能优化
- [ ] 降低 CPU 占用率（优化计算频率）
- [ ] 添加消息处理延迟监控
- [x] 实现动态参数调整

## 测试验证
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 与实际底盘硬件联调测试
- [ ] 不同手柄型号兼容性测试
- [ ] 长时间稳定性测试

## 文档完善
- [ ] 添加使用示例和教程
- [ ] 编写故障排查指南
- [ ] 提供参数调优建议

## 已知问题
- [ ] Y 轴方向可能需要根据实际底盘调整符号
- [ ] 旋转和平移的权重分配可能需要优化
- [ ] 死区阈值可能需要根据不同手柄校准

## 2026-05-27 200 cm/s 保护问题

- [x] 记录 `200 cm/s` 档位导致底盘突然断反应的问题
- [x] 曾临时将默认速度档位从 10/20/60/100/200/400 改为 10/20/40/60/100/150 cm/s
- [x] 保持 `local_navigation_node max_wheel_speed_rad_s = 64.0 rad/s` 不变
- [ ] 重新实机验证持续 hold 左摇杆后轮速变弱问题
- [ ] 若要恢复 200 cm/s，必须先完成电源和驱动器保护原因排查

## 2026-05-27 恢复速度档位复测

- [x] 曾按用户要求恢复默认速度档位到 10/20/60/100/200/400 cm/s 用于对比测试
- [x] 确认本次未修改 `max_wheel_speed_rad_s`、watchdog、左摇杆映射或运动学参数
- [ ] 复测持续 hold 左摇杆后轮速变弱问题是否仍存在

## 2026-05-28 ROS domain 隔离后恢复 150 档位

- [x] 确认底盘异常主要来自 R1/R2 ROS2 domain 混线，而不是 joystick `128/512` 映射
- [x] 将默认速度档位设置为 10/20/40/60/100/150 cm/s
- [x] 保持 `local_navigation_node max_wheel_speed_rad_s = 64.0 rad/s` 不变
- [ ] 在 `ROS_DOMAIN_ID=1`、`ROS_LOCALHOST_ONLY=1` 下复测 100/150 cm/s 连续运行

## 2026-06-06 固定 150 cm/s 混合三次曲线

- [x] `max_speed_cm` 默认改为 `150.0 cm/s`
- [x] 新增 `translation_linear_weight = 0.2`
- [x] 平移曲线实现 `y = 0.2x + 0.8x³`
- [x] 移除 START/SELECT 速度档切换逻辑
- [x] 保持右摇杆旋转为线性映射
- [x] 保持 joystick input watchdog 与轮速 acceleration limit 不变
- [ ] R1 离地测试 10%/25%/50%/75%/100% 摇杆幅度
- [ ] R1 落地低风险区域测试起步摩擦和中段手感

## 2026-06-07 Deadzone 调整

- [x] `joystick_bridge deadzone` 从 `24` 改为 `15`
- [x] 与 `my_joystick_driver` 上游 deadzone 同步
- [x] 保持 Motor 7 `trigger_deadzone = 24` 不变
- [ ] 实机确认摇杆回中时底盘不会自行漂移

## 2026-06-07 混合曲线权重调整

- [x] `translation_linear_weight` 默认从 `0.2` 改为 `0.1`
- [x] 当前平移曲线更新为 `y = 0.1x + 0.9x³`
- [x] 保持 `max_speed_cm = 150.0 cm/s` 与 `deadzone = 15` 不变
- [x] 保持右摇杆旋转、watchdog 和底层轮速限制不变
- [ ] 实机确认 10% 至 50% 推杆范围的低速微操效果

## 2026-06-07 右摇杆旋转混合曲线

- [x] `max_rotation` 当前默认改为 `1.2 rad/s`
- [x] 新增 `rotation_linear_weight = 0.1`
- [x] 旋转曲线实现 `y = 0.1x + 0.9x³`
- [x] 保持 `deadzone = 15` 和 `input_timeout_sec = 0.3 s` watchdog 不变
- [ ] 离地确认右摇杆旋转方向和满杆速度
- [ ] 落地确认低速旋转微操效果


## v2.0 手動人視角座標

- [x] 十字鍵改為 E-stop 在人視角中的四方向絕對選擇
- [x] 左搖桿平移由人視角轉換為車體座標
- [x] 保持右搖桿旋轉、速度曲線和底盤限幅不變
- [x] 左搖桿未回中時拒絕視角切換
- [x] 新增 `/view_orientation` 狀態 topic
- [x] 保留 `input_timeout_sec=0.3 s` 停車 watchdog
- [x] 新增四方向與十字鍵映射單元測試
- [x] 實機確認 E-stop 在左時，左搖桿向前仍向人視角前方平移
- [x] 實機確認四個方向及斜向移動
- [ ] 評估日後加入 IMU 自動更新視角
