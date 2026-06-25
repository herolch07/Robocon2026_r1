> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

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


## v13 Motor7/8 双 arm 气动选择控制

- [x] bridge 订阅 `/motor_position_selector_status`
- [x] A/B 根据当前 Motor7/8 选择路由
- [x] SELECT 仅控制 Motor8 inclination
- [x] Motor7 与 Motor8 分别保存锁定状态
- [x] 五位 arm command 默认安全值改为 `[0,1,0,1,1]`
- [x] 保留 `input_timeout_sec=0.3 s` watchdog
- [x] 新增 selector 索引、安全状态和上升沿测试
- [ ] 实机确认 START 切换后 A/B 只改变所选 arm
- [ ] 实机确认 SELECT 只改变 Motor8 inclination
- [ ] 实机确认 joystick 断开后所有 arm 回到安全状态

## v14 七路 Arduino panel 相容性

- [x] 確認本 bridge 仍發布五路 `/pneumatic_gripper_cmd`
- [x] 確認七路 serial output 由 `kfs_staff_gripper_arduino_node` 合併處理
- [x] 保持 A/B/SELECT 與 Motor7/8 selector 邏輯不變
- [x] 記錄 Relay 7 / Pin 28 暫時不由本 package 控制
- [ ] Relay 7 用途確認後，再評估是否需要本 package 新增一個控制欄位

## v15 Motor7 inclination

- [x] 將 Relay 7 / Pin 28 記錄為 Motor7 inclination
- [x] `/pneumatic_gripper_cmd` 從五路擴為六路
- [x] `DEFAULT_ARM_SAFE_STATE` 改為 `[0,1,0,1,1,0]`
- [x] SELECT 改為控制目前選中 arm 的 inclination
- [x] 新增 selected inclination index 測試
- [ ] 實機確認 Motor7/Motor8 切換後 SELECT 只作用於選中 arm


## 2026-06-19 STAFF/KFS operation mode pneumatic 鍵位

- [x] `pneumatic_gripper_joystick_bridge_node` 訂閱 `/operation_mode`
- [x] 只有 STAFF mode 接受 pneumatic 按鍵
- [x] `A` 改為 Motor7 height toggle
- [x] `Y` 改為 Motor8 height toggle
- [x] `R1` 改為 Motor7 inclination/head toggle
- [x] `L1` 改為 Motor8 inclination/head toggle
- [x] `SELECT/START` 不再控制 pneumatic，避免與 mode 切換衝突
- [x] 保持 joystick timeout 後回 safe state
- [ ] 實機確認四個 pneumatic 鍵位與 relay 方向


## 2026-06-19 五路 relay staff pneumatic 鍵位

- [x] `/pneumatic_gripper_cmd` 從六路改為四路
- [x] 移除 Motor7/Motor8 height relay 相關 A/Y 控制
- [x] STAFF mode 下 `B` 控 Motor7 staff gripper relay
- [x] STAFF mode 下 `X` 控 Motor8 staff gripper relay
- [x] STAFF mode 下 `R1` 控 Motor7 inclination/head relay
- [x] STAFF mode 下 `L1` 控 Motor8 inclination/head relay
- [x] `DEFAULT_ARM_SAFE_STATE` 更新為 `[1,0,1,0]`
- [x] 更新五路 pneumatic command 測試
- [ ] 實機確認 X/B 同時驅動 position preset 與 gripper relay 的效果符合機構需求


## 2026-06-19 STAFF gripper relay 改為 A/Y

- [x] STAFF mode 下 `Y` 改為 Motor7 gripper relay toggle
- [x] STAFF mode 下 `A` 改為 Motor8 gripper relay toggle
- [x] 移除 `B/X` 作為 gripper relay 鍵位
- [x] 移除 `L1/R1` 作為 inclination relay 鍵位，避免和 trim 衝突
- [ ] 實機確認 A/Y 同時觸發 position preset 與 gripper relay 的時序可接受


## 2026-06-19 STAFF head relay moved to L3/R3

- [x] STAFF mode 下 `R3` 控 Motor7 inclination/head relay
- [x] STAFF mode 下 `L3` 控 Motor8 inclination/head relay
- [x] 保持 `L1/R1/L2/R2` 作 Motor7/8 manual trim
- [x] 更新 inclination index 測試
- [ ] 實機確認 L3/R3 抬頭方向與 relay 狀態


## 2026-06-19 Final STAFF Gripper / 90-Degree Split

This section supersedes any same-day text that says Y/A also toggle gripper relays.

Current STAFF mode split:

```text
Y  -> Motor7 left-right 90-degree / preset cycle only
A  -> Motor8 left-right 90-degree / preset cycle only
B  -> Motor7 staff gripper relay toggle only
X  -> Motor8 staff gripper relay toggle only
R1 -> Motor7 manual trim negative
R2 -> Motor7 manual trim positive
L1 -> Motor8 manual trim negative
L2 -> Motor8 manual trim positive
R3 -> Motor7 head / inclination relay toggle
L3 -> Motor8 head / inclination relay toggle
```

Current KFS mode remains:

```text
Y  -> KFS gripper toggle
L2 -> Motor6 horizontal positive / out
R2 -> Motor6 horizontal negative / in
L1 -> Motor5 elevator negative / down
R1 -> Motor5 elevator positive / up
```


## 2026-06-19 Final STAFF ABXY Layout

最新 STAFF mode ABXY：

```text
A -> Motor7 左右 90° / preset cycle only
X -> Motor8 左右 90° / preset cycle only
B -> Motor7 staff gripper relay toggle only
Y -> Motor8 staff gripper relay toggle only
```

其他 STAFF 鍵位不變：`R1/R2=Motor7 微調`，`L1/L2=Motor8 微調`，`R3=Motor7 抬頭`，`L3=Motor8 抬頭`。

KFS mode 不變：`Y=KFS gripper`，`L2/R2=horizontal positive/negative`，`L1/R1=elevator negative/positive`。


## 2026-06-19 現行五路 STAFF relay 確認

- [x] `/pneumatic_gripper_cmd` 固定為 `[M7 gripper, M8 inclination, M8 gripper, M7 inclination]`
- [x] STAFF mode `B=Motor7 gripper`、`Y=Motor8 gripper`
- [x] STAFF mode `R3/P1=Motor7 inclination`、`L3/P2=Motor8 inclination`
- [x] `A/X` 不再同時切 gripper relay，只交給 position bridge 控制 preset
- [ ] 實機確認 Arduino 五路 relay 實際線序與文件一致：`[KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`

## 2026-06-20 STAFF D-pad Down Relay Swap

- [x] `pneumatic_gripper_joystick_bridge_node` subscribes to `/view_orientation`
- [x] `/view_orientation=2` swaps Motor7/Motor8 gripper and inclination relay buttons
- [x] `/view_orientation=0/1/3` keeps normal relay mapping
- [x] Add no-hardware unit tests for pneumatic button swap helper
- [ ] Real robot test: D-pad down swaps B/Y and P1/P2 relay targets correctly

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
