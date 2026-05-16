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
- [x] 根据实机测试将 `lateral_axis_sign` 默认值校准为 `-1.0`，使左摇杆向左对应左平移

## 待完成

- [ ] 将 `damiao_node` 拆分到独立 `damiao_driver` package，避免底盘 package 承担全机器人电机 driver 职责
- [ ] 将 `local_navigation_node` 参数整理到 YAML/launch 文件
- [ ] 将 `damiao_node` motor_id 映射改成 YAML/launch 参数
- [ ] 为 `local_navigation_node` 增加自动化测试
- [ ] 为 `damiao_node` 增加无硬件 mock 测试
- [ ] 整理旧 VESC 节点，确认是否仍属于当前 R1/R2 工程范围
