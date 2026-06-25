> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

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

## 2026-06-13 Motor 7/8 共享位置控制

- [x] Motor 7 复用 Motor 8 的位置 controller 实现，不复制控制算法
- [x] Motor 7 默认参数暂与 Motor 8 完全相同
- [x] 新增共享 selector，启动默认选择 Motor 7
- [x] START 在 Motor 7/8 之间切换
- [x] X 控制当前电机 A/B 切换
- [x] L2/R2 按压深度控制当前电机正反微调
- [x] X/L2/R2 未释放时禁止 START 切换
- [x] 未选中的电机保持自己的目标位置
- [x] 主启动脚本停用 Motor 7 旧 VEL controller/bridge
- [x] 新增 selector 与 Motor 7 POS_VEL 无硬件测试
- [ ] 实机确认启动后默认控制 Motor 7
- [ ] 实机确认 START 切换后只控制所选电机
- [ ] 根据 Motor 7 真实机构重新确定 A/B、软限位和速度

## 2026-06-13 Motor 7/8 三位置

- [x] 新增 `position_c_rad = -35.0 rad`
- [x] `position_b_rad` 由 `33.0 rad` 调整为 `35.0 rad`
- [x] X 改为 `0 -> +35 -> -35 -> 0` 三位置循环

## v12 Motor7/8 POS_VEL 目标收窄到 32 rad

- [x] `position_b_rad` 由 `35.0 rad` 调整为 `32.0 rad`
- [x] `position_c_rad` 由 `-35.0 rad` 调整为 `-32.0 rad`
- [x] 软限位由 `-35.0..35.0 rad` 调整为 `-32.0..32.0 rad`
- [ ] 实机确认 Motor7/8 在 `0/+32/-32 rad` 三点循环下不会撞限位
- [x] Motor 7/8 分别保存自己的三位置索引
- [x] 新增三位置循环无硬件测试
- [ ] 实机确认 Motor 7 三个位置顺序和方向
- [ ] 实机确认 Motor 8 三个位置顺序和方向


## v9 Motor6 L3／R3 固定速度

- [x] Motor6 移動由十字鍵搬到 L3／R3
- [x] 移除 Motor6 十字鍵速度檔切換
- [x] 固定命令速度預設為 `10 rad/s`
- [x] L3／R3 同時按下或全部鬆開時輸出零速
- [x] 保留下游 `0.3 s` command watchdog
- [x] 新增正向、負向、衝突停止單元測試
- [x] 實機確認 L3／R3 對應的 Motor6 正負方向
- [x] 實機確認固定 `10 rad/s` 操作速度合適

## v10 Motor6 P1／P2 背鍵替代操作

- [x] 使用 `evtest` 確認 P1／P2 目前沒有獨立 evdev event
- [x] 將 8BitDo P1 remap 為 R3
- [x] 將 8BitDo P2 remap 為 L3
- [x] 確認 source code 不需要新增 `p1/p2` 欄位
- [x] 更新 Motor6 horizontal 操作文檔


## 2026-06-19 STAFF/KFS operation mode

- [x] `motor_position_selector_joystick_bridge_node` 訂閱 `/operation_mode`
- [x] 移除 START 作為 Motor7/Motor8 selector 的現行用途
- [x] STAFF mode 下 `X` 直接控制 Motor8 preset/open-close cycle
- [x] STAFF mode 下 `B` 直接控制 Motor7 preset/open-close cycle
- [x] STAFF mode 下 `L2` 直接控制 Motor8 trim
- [x] STAFF mode 下 `R2` 直接控制 Motor7 trim
- [x] operation mode 無效或 timeout 時發布 invalid neutral input
- [x] `elevator_joystick_bridge_node` 預設停用 L1/R1 legacy elevator mapping
- [x] 新增直接 trim 映射單元測試
- [ ] 實機確認 STAFF mode 下 X/B/L2/R2 對應 Motor8/Motor7 正確


## 2026-06-19 KFS mode elevator/horizontal

- [x] `elevator_joystick_bridge_node` 訂閱 `/operation_mode`
- [x] KFS mode 下 `L1/R1` 控制 Motor5 elevator 升降
- [x] STAFF mode 下 elevator bridge 發布 `0.0`，避免和 pneumatic 抬頭衝突
- [x] `horizontal_joystick_bridge_node` 訂閱 `/operation_mode`
- [x] KFS mode 下 `L2/R2` 控制 Motor6 horizontal 出入
- [x] STAFF mode 下 horizontal bridge 發布 `0.0`，避免和 Motor7/8 trim 衝突
- [x] 新增 horizontal trigger 與 elevator button 單元測試
- [ ] 實機確認 L1/R1 升降方向，必要時交換符號
- [ ] 實機確認 L2/R2 出入方向，必要時交換符號


## 2026-06-19 STAFF mode A/Y 90-degree 與 L/R 微調

- [x] STAFF mode 下 `Y` 改為 Motor7 preset / 90-degree cycle
- [x] STAFF mode 下 `A` 改為 Motor8 preset / 90-degree cycle
- [x] STAFF mode 下 `R1/R2` 改為 Motor7 negative/positive trim
- [x] STAFF mode 下 `L1/L2` 改為 Motor8 negative/positive trim
- [x] 移除 `B` 作為 Motor7 staff position 鍵，避免與既有 90-degree turn 衝突
- [x] KFS mode horizontal 對調為 `L2 positive/out`、`R2 negative/in`
- [x] 更新 position trim 與 horizontal trigger 單元測試
- [ ] 實機確認 R1/R2、L1/L2 微調方向是否符合機手直覺
- [ ] 實機確認 A/Y 90-degree cycle 是否對應正確 motor


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


## 2026-06-19 現行 STAFF/KFS 鍵位確認

- [x] `motor_position_selector_joystick_bridge_node` 更新為 STAFF mode `A=Motor7 preset`、`X=Motor8 preset`
- [x] `R1/R2` 保留為 Motor7 微調，`L1/L2` 保留為 Motor8 微調
- [x] KFS mode `L2/R2` 控制 Motor6 horizontal positive/negative
- [x] KFS mode `L1/R1` 控制 Motor5 elevator negative/positive
- [ ] 實機再次確認 Motor7/Motor8 90° preset 的機械角度是否需要由 32 rad 改為更精準值

## 2026-06-19 Motor5 elevator speed increase

- [x] Increase `elevator_joystick_bridge_node.command_speed_rad_s` from `3.0` to `28.0`
- [x] Increase `elevator_controller_node.max_speed_rad_s` from `3.0` to `28.0`
- [x] Keep KFS-only mode gate and `timeout_sec=0.3 s` unchanged
- [ ] Test Motor5 elevator at 28.0 rad/s with mechanism clear of hard stops

## 2026-06-20 KFS mechanism speed parameters

- [x] Motor5 elevator bridge default `command_speed_rad_s = 28.0`
- [x] Motor5 elevator controller default `max_speed_rad_s = 28.0`
- [x] Motor6 horizontal bridge default `command_speed_rad_s = 30.0`
- [x] Motor6 horizontal controller default `max_speed_rad_s = 30.0`
- [x] Keep KFS-only `/operation_mode=2` gate and `timeout_sec=0.3 s` unchanged
- [ ] Test Motor5 elevator at `28.0 rad/s` with mechanism clear of hard stops
- [ ] Test Motor6 horizontal at `30.0 rad/s` with mechanism clear of hard stops

## 2026-06-20 STAFF D-pad Down Motor7/Motor8 Swap

- [x] `motor_position_selector_joystick_bridge_node` subscribes to `/view_orientation`
- [x] `/view_orientation=2` swaps Motor7/Motor8 position preset and trim mapping
- [x] `/view_orientation=0/1/3` keeps normal Motor7/Motor8 mapping
- [x] Add no-hardware unit test for position swap helper
- [ ] Real robot test: STAFF mode D-pad up normal mapping, D-pad down swapped mapping

## 2026-06-20 STAFF D-pad Down Trim Direction Update

- [x] D-pad down swaps Motor7/Motor8 position targets
- [x] D-pad down also reverses each trim pair: `R1/R2` and `L1/L2`
- [x] Add no-hardware unit test for trim swap and direction reversal
- [ ] Real robot test D-pad down: `R1=Motor8 positive`, `R2=Motor8 negative`, `L1=Motor7 positive`, `L2=Motor7 negative`

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
