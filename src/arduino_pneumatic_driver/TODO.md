# arduino_pneumatic_driver TODO

## 已完成

- [x] 新增 Arduino pneumatic driver package
- [x] 实现 `pneumatic_relay_driver_node`
- [x] 实现 `pneumatic_gripper_joystick_bridge_node`
- [x] 使用 Arduino 已测试协议 `[0,0]` / `[1,1]`
- [x] 默认使用稳定串口 `/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0`
- [x] 实现 timeout 后发送 safe state `[1,1]`
- [x] README 记录 topic、参数、timeout、安全状态和最小测试
- [x] 分离 D9 gripper open/close 与 D8 height high/low 控制
- [x] pneumatic joystick bridge 改为 20Hz 持续发布当前状态，避免 relay 闪烁
- [x] 回退持续发布方案，只保留 B 控制 gripper open，D8 保持 HIGH
- [x] 按新需求改为初始 height LOW，按 A 后 height HIGH 并保持
- [x] 增加 X 锁定 height LOW，直到再次按 A

## 待完成

- [ ] 增加 launch 文件和 YAML 参数文件
- [x] 旧 `[1,0]` 启动策略已被新接线废弃；当前 timeout/startup 使用 `[1,1]` = CLOSE + HIGH
- [ ] 增加 Arduino PING/PONG 心跳协议
- [ ] 增加无硬件 serial mock 测试
- [ ] 后续如 valve 数量增加，将 command message 升级为自定义 msg

## v7 新 relay 接线映射

- [x] v7 假设 `A` 控 arm gripper OPEN latch，后续 v9 实机确认已覆盖
- [x] v7 假设 `X` 控 arm gripper CLOSE latch，后续 v9 实机确认已覆盖
- [x] v7 假设 `B` 控 height，后续 v9 实机确认已覆盖
- [x] joystick timeout 后输出 `[1,1]`，避免 height LOW 被保持
- [x] 文档同步当前 A/X/B 控制语义

## v8 启动默认 height LOW

- [x] `initial_height_state` 改为 `0`
- [x] v8 standalone pneumatic driver `safe_state` 曾改为 `[1,0]`，v10 已按 relay 顺序修正为 `[0,1]`
- [x] joystick timeout 后回 `[1,0]`
- [x] v8 启动默认 LOW 逻辑保留；v9 后 B 不再控制 height

## v9 实机确认 B/A/X 映射

- [x] `B` 控 arm gripper：按住 OPEN，松开 CLOSE
- [x] `A` 控 arm height LOW
- [x] `X` 控 arm height HIGH
- [x] startup/timeout 保持 `[1,0]` = CLOSE + LOW

## v10 relay 顺序实机确认

- [x] `/pneumatic_gripper_cmd` 顺序改为 `[height_state, gripper_state]`
- [x] startup/timeout safe state 改为 `[0,1]`
- [x] `B` 只控制 gripper，`A/X` 只控制 height

## v11 arm height 单键切换

- [x] 将 `A=LOW`、`X=HIGH` 改为默认 `A` 单键切换 LOW/HIGH
- [x] 使用按钮上升沿切换，避免长按时按 joystick 发布频率反复翻转
- [x] 新增 `height_toggle_button` 参数，允许通过参数更换按钮
- [x] timeout 后回到 `[0,1]`，并要求切换按钮先松开再重新按下
- [x] 新增无硬件单键切换测试
- [x] README 追加 v11 当前映射与串口协议说明
- [ ] 实机确认每按一次 `A` 只切换一次高度，`X` 已释放

## v12 arm gripper 单键锁定与默认 OPEN

- [x] 将 `B` 从按住 OPEN 改为每次按下切换 OPEN/CLOSE
- [x] 使用 B 按钮上升沿，避免长按时重复切换
- [x] arm bridge 启动和 joystick timeout 默认改为 `[0,0]` = LOW + OPEN
- [x] timeout 后要求 A/B 先松开再重新按下
- [x] standalone pneumatic driver `safe_state` 改为 `[0,0]`
- [x] 新增 B 锁定切换与 timeout 恢复测试
- [x] README 追加 v12 当前行为和释放夹持物风险
- [ ] 实机确认启动默认 OPEN、B 每按一次只切换一次
- [ ] 实机确认 joystick timeout 后 arm gripper OPEN 符合机构安全要求
