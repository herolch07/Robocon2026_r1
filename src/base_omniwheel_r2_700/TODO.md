# base_omniwheel_r2_700 TODO

## 已完成

- [x] 实现 `local_navigation_node` 四轮全向底盘逆运动学
- [x] 实现 `damiao_node` 达妙电机 VEL 模式控制
- [x] 支持 Motor 1-7 初始化
- [x] 修复轮径换算，使用 `63.5 mm` 全向轮半径
- [x] 增加 `local_navigation_node` 输入 timeout，`/local_driving` 中断后 Motor 1-4 归零
- [x] 增加 `damiao_node` 电机级 watchdog，连续 VEL 命令超时后对应电机归零
- [x] README 追加 2026-05-14 安全更新说明

## 待完成

- [ ] 将 `damiao_node` 拆分到独立 `damiao_driver` package，避免底盘 package 承担全机器人电机 driver 职责
- [ ] 将轮距、轮径、电机方向、motor_id 映射改成 YAML/launch 参数
- [ ] 为 `local_navigation_node` 增加自动化测试
- [ ] 为 `damiao_node` 增加无硬件 mock 测试
- [ ] 整理旧 VESC 节点，确认是否仍属于当前 R1/R2 工程范围
