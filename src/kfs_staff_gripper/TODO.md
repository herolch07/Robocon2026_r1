# kfs_staff_gripper TODO

## v0.1.0 初始版本

- [x] 新增 `kfs_staff_gripper` ROS2 Python package
- [x] 新增 `kfs_staff_gripper_arduino_node`
- [x] 新增 `kfs_staff_gripper_joystick_bridge_node`
- [x] 支持 Arduino 四路 relay command `[r1,r2,r3,r4]`
- [x] 兼容现有 `/pneumatic_gripper_cmd`，统一管理同一个 Arduino serial port
- [x] 新增 `/kfs_staff_gripper_cmd` topic
- [x] 新增 `/kfs_staff_gripper_status` topic
- [x] 实现 arm pneumatic 与 KFS staff gripper 独立 command timeout，避免一个 topic 掩盖另一个 topic 的 watchdog
- [x] 实现 joystick timeout 后发布 staff safe_state
- [x] README 记录 topic、参数、启动方式、超时保护和 Arduino 注意事项
- [x] 更新 `r1_start_base_1_0.sh`，用四路 aggregator 替换旧 serial driver 并启动 KFS bridge

## 待实机确认

- [x] R3 relay 4 预留通道已取消：Arduino sketch 已改为三路 relay，当前 controller 不再使用 R3 控制 KFS
- [x] 确认 Y 控制的 KFS staff gripper 通道：按住 OPEN，松开 CLOSE
- [x] 确认 safe/default state `[0,0]` 对应 staff gripper CLOSE
- [x] 确认 `Y` 作为 staff gripper hold-to-open 按键可用
- [ ] 根据实机动作决定是否需要 latch 模式，而不是 hold-to-enable 模式
- [ ] 给 Arduino sketch 增加 millis watchdog，避免 USB 断线后 relay 保持最后状态

## v0.3.0 三路 relay sketch 适配

- [x] Arduino protocol 从四路 `[r1,r2,r3,r4]` 更新为三路 `[r1,r2,r3]`
- [x] relay pin 约定更新为 D8/D9/D10，三路均为高电平触发
- [x] `/pneumatic_gripper_cmd` 继续映射 relay 1-2
- [x] `/kfs_staff_gripper_cmd` 改为单值 `[staff_gripper_state]`，映射 relay 3
- [x] `kfs_staff_gripper_joystick_bridge_node` 改为只使用 `Y`，按住 OPEN，松开 CLOSE
- [x] `R3` 不再由 KFS staff gripper node 使用
- [x] ROS 侧 watchdog safe_state 更新为 `[0,0,0]`

## 后续优化

- [ ] 如确认接线固定，增加 launch 文件统一启动 arm pneumatic bridge、KFS bridge 和 Arduino aggregator
- [ ] 根据比赛流程增加明确的 staff gripper safe_state 命名参数
- [ ] 增加 relay 状态到更结构化的 status topic

## v0.3.1 arm pneumatic 新接线 safe state

- [x] aggregator `safe_state` 改为 `[1,1,0]`
- [x] arm pneumatic timeout 后回到 gripper CLOSE + height HIGH
- [x] 保持 KFS staff gripper `Y` 控制不变

## v0.3.2 arm height 启动默认 LOW

- [x] aggregator `safe_state` 改为 `[0,1,0]`
- [x] arm pneumatic startup/reconnect/shutdown 默认 height LOW
- [x] 保持 KFS staff gripper `Y` 控制不变

## v0.3.3 arm pneumatic 实机按键确认

- [x] `B` 控 arm gripper：按住 OPEN，松开 CLOSE
- [x] `A` 控 arm height LOW
- [x] `X` 控 arm height HIGH
- [x] v0.3.3 当时记录为 `[1,0,0]`，v0.3.4 已修正为 `[0,1,0]`

## v0.3.4 arm relay 顺序实机确认

- [x] arm relay 顺序确认并记录为 `[height_state, gripper_state]`
- [x] aggregator safe_state 改为 `[0,1,0]`

## v0.3.5 Arduino serial auto-detect

- [x] 新 Arduino Mega by-id 不同时自动扫描 Arduino/CH340 serial path
- [x] 自动扫描时排除达妙 USB-CAN `HDSC`
- [x] README 记录换 Arduino Mega 后的串口排查方式

## v0.3.6 arm 默认 OPEN、KFS 默认 CLOSE

- [x] aggregator 默认 `safe_state` 改为 `[0,0,0]`
- [x] 明确 relay 顺序为 `[arm_height, arm_gripper, kfs_gripper]`
- [x] 保持 KFS bridge `safe_state=[0]`，启动和 timeout 默认 CLOSE
- [x] 保持 Y 为按住 OPEN、松开 CLOSE，不改为 latch
- [x] 新增三路默认状态无硬件测试
- [x] README 追加 v0.3.6 当前按钮和 watchdog 行为
- [ ] 实机确认 bash 启动后 arm OPEN、KFS CLOSE
- [ ] 实机确认 B latch 与 Y hold 两种操作互不影响
