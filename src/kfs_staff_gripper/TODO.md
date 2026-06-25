> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

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

## v0.3.7 KFS Y 单键锁定切换

- [x] 将 Y 从按住 OPEN 改为每次按下切换 OPEN/CLOSE
- [x] 使用 Y 按钮上升沿，避免长按时重复切换
- [x] 保持启动和 timeout 默认 `[0]` = KFS CLOSE
- [x] timeout 后要求 Y 先松开再重新按下
- [x] 保持 aggregator 默认 `[0,0,0]` 和 relay 映射不变
- [x] 新增 KFS Y 锁定与 timeout 恢复测试
- [x] README 追加 v0.3.7 当前行为
- [ ] 实机确认 Y 每按一次只切换一次，松开后保持当前状态
- [ ] 实机确认 joystick timeout 后 KFS 自动 CLOSE


## v0.4.0 六路双 arm relay panel

- [x] relay panel 从三路扩展为六路严格串口协议
- [x] 固定 relay 1-6 与 Pin 22-27 的实机功能顺序
- [x] 默认安全状态改为 `[0,0,1,0,1,1]`
- [x] `/pneumatic_gripper_cmd` 映射 relay 2-6
- [x] `/kfs_staff_gripper_cmd` 映射 relay 1
- [x] 无效长度 command 不再刷新 watchdog
- [x] 新增六路格式、安全状态和旧协议拒绝测试
- [ ] 实机确认 Arduino 回报 `Command OK`
- [ ] 实机逐路确认 Relay 1-6，不连接危险负载时先测试
- [ ] Arduino sketch 增加本地 `millis()` 通信 watchdog

## v0.4.1 七路 relay panel

- [x] Arduino serial protocol 從六路 `[r1,r2,r3,r4,r5,r6]` 更新為七路 `[r1,r2,r3,r4,r5,r6,r7]`
- [x] `RELAY_COUNT` 改為 `7`
- [x] 預設完整安全狀態改為 `[0,0,1,0,1,1,0]`
- [x] 保持 `/pneumatic_gripper_cmd` 為五路，不改現有手柄按鍵
- [x] 保持 `/kfs_staff_gripper_cmd` 為一路
- [x] Relay 7 / Pin 28 暫時標記為 reserved，安全值 `0`
- [x] 更新七路格式與安全狀態測試
- [ ] 確認 Relay 7 / Pin 28 實際接線用途與 `0/1` 安全語義
- [ ] Relay 7 用途確認後，再決定是否新增 topic 或手柄按鍵
- [ ] 實機確認 Arduino 回報七路 `Command OK`

## v0.4.2 Relay 7 = Motor7 inclination

- [x] 確認 Relay 7 / Pin 28 用作 Motor7 inclination
- [x] `/pneumatic_gripper_cmd` 從五路擴為六路
- [x] `arm_relay_indices` 從 `[1,2,3,4,5]` 更新為 `[1,2,3,4,5,6]`
- [x] SELECT 改為控制目前選中 arm 的 inclination
- [x] 保持完整 safe_state `[0,0,1,0,1,1,0]`
- [ ] 實機確認 START 選中 Motor7 時 SELECT 只切換 Motor7 inclination
- [ ] 實機確認 START 選中 Motor8 時 SELECT 只切換 Motor8 inclination


## 2026-06-19 KFS mode gating

- [x] `kfs_staff_gripper_joystick_bridge_node` 訂閱 `/operation_mode`
- [x] 只有 KFS mode 接受 Y 鍵切換 KFS gripper
- [x] STAFF mode 下忽略 Y，避免和 Motor8 height 鍵位衝突
- [x] 保持 joystick timeout 後回 safe state
- [ ] 實機確認 START 切 KFS mode 後 Y 才控制 KFS gripper
- [ ] 實機確認 SELECT 切 STAFF mode 後 Y 不再控制 KFS gripper


## 2026-06-19 五路 Arduino relay 協議

- [x] Arduino serial protocol 改為五路 `[r1,r2,r3,r4,r5]`
- [x] relay pins 更新為 `{22,24,25,27,28}` 對應 ROS 順序 `[KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`
- [x] `DEFAULT_SAFE_STATE` 更新為 `[0,1,0,1,0]`
- [x] `/pneumatic_gripper_cmd` 改為四路，映射 relay 2-5
- [x] `/kfs_staff_gripper_cmd` 保持一路，映射 relay 1
- [x] 更新五路 protocol 單元測試
- [ ] 實機確認 Arduino 收到 `[0,1,0,1,0]` 時所有 relay 安全狀態正確


## 2026-06-19 五路 Arduino 聚合確認

- [x] Arduino serial 聚合順序更新為 `[KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`
- [x] KFS gripper `Y` 只在 `/operation_mode=2` 時生效
- [x] 全系統 relay safe state 記錄為 `[0,1,0,1,0]`
- [ ] 實機長時間測試 KFS/STAF mode 來回切換時 relay 不誤動作

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
