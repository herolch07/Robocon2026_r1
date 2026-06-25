> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md) 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# R1 测试指南

本文件记录当前工作区内的测试方式。旧路径 `Robocon2026_r2/2026R2_ws` 和旧脚本 `start_full_control_chain.sh` 已不再作为当前 R1 流程使用。

## 1. 编译检查

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --symlink-install
source install/setup.bash
```

## 2. 启动完整系统

```bash
./r1_start_base_1_0.sh
```

如果只做无硬件 topic 级检查，可以分别启动相关节点，而不启动硬件 driver。

## 3. 手柄链路测试

查看手柄输入：

```bash
ros2 topic echo /joystick_data
```

预期范围：

```text
lx/ly/rx/ry: -512 .. 512
dx/dy: -512, 0, 512
l2/r2: 0 .. 512
```

查看底盘桥接输出：

```bash
ros2 topic echo /local_driving
```

格式：

```text
data[0] = direction_rad
data[1] = speed_cm_per_sec
data[2] = rotation_rad_per_sec
```

## 4. 底盘测试

先确认低速默认值：

```bash
ros2 param get /joystick_bridge max_speed_cm
ros2 param get /joystick_bridge max_rotation
```

当前默认应为：

```text
max_speed_cm = 150.0
translation_linear_weight = 0.1
max_rotation = 3.0
rotation_linear_weight = 0.1
```

手动发布小速度测试：

```bash
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [1.5708, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [-1.5708, 10.0, 0.0]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 0.3]}"
ros2 topic pub --once /local_driving std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0, 0.0]}"
```

预期：

```text
0 rad: 前进
+pi/2: 右移
-pi/2: 左移
rotation: 原地旋转
```

如果旋转方向相反：

```bash
ros2 param set /local_navigation_node rotation_axis_sign -1.0
```

## 5. 机械臂执行机构测试

升降：

```bash
ros2 topic pub --once /elevator_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.5]}"
ros2 topic echo /elevator_status
```

水平：

```bash
ros2 topic pub --once /horizontal_speed_cmd std_msgs/msg/Float32MultiArray "{data: [1.0]}"
ros2 topic echo /horizontal_status
```

Motor7 / Motor8 staff position controller：

```bash
ros2 topic echo /motor7_position_status
ros2 topic echo /motor8_position_status
ros2 topic echo /motor_position_selector_status
```

目前 Motor7/8 走 POS_VEL，不再用旧 `/arm_gripper_speed_cmd` 速度 topic。實機動作測試應優先用手柄 STAFF mode 的 `A/X` preset 和 `R1/R2/L1/L2` trim；不要在 start base 同時啟動舊 `arm_gripper_controller_node`。

这些速度命令只发布一次时，controller 会在 `timeout_sec = 0.3s` 后自动归零；Motor7/8 position controller 由自身 input/feedback timeout 保护。

## 6. Pneumatic Gripper 测试

确认 Arduino 串口：

```bash
ls -l /dev/serial/by-id/
```

当前默认：

```text
/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0
```

发布命令：

```bash
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0, 0]}"
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 0]}"
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1, 1]}"
ros2 topic echo /pneumatic_gripper_status
```

含义：

```text
D9: 0 OPEN, 1 CLOSE
D8: 0 LOW, 1 HIGH
safe_state = [1,0]
```

## 7. Watchdog 测试

可以通过停止上游节点验证下游会归零：

```bash
ros2 param get /joystick_bridge input_timeout_sec
ros2 param get /local_navigation_node command_timeout_sec
ros2 param get /motor_controller_node command_timeout_sec
```

预期：

```text
joystick_bridge: 0.3s 后发布 /local_driving = [0,0,0]
local_navigation_node: 0.3s 后 Motor 1-4 归零
damiao_node: 0.5s 后对应连续 VEL 电机归零
```

## 8. 测试记录表

| 测试项目 | 预期结果 | 实际结果 | 通过/失败 | 备注 |
|---------|---------|---------|----------|------|
| 手柄连接 | `/joystick_data` 有 -512..512 数据 | | | |
| 底盘前后 | 左摇杆上/下正确 | | | |
| 底盘横移 | 左摇杆左/右正确 | | | |
| 底盘旋转 | 右摇杆左/右原地旋转 | | | |
| Motor 5 | L1/R1 固定速度升降有响应 | | | |
| Motor 6 | D-pad 左/右有响应 | | | |
| Motor 7 | L2/R2 模拟调速有响应 | | | |
| Pneumatic | A/B/X 状态正确 | | | |
| Timeout | 停止输入后自动归零 | | | |

## ROS2 domain isolation check

测试前确认 R1 已隔离：

```bash
echo $ROS_DOMAIN_ID
echo $ROS_LOCALHOST_ONLY
ros2 node list
ros2 topic list
```

R1 不应看到 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control`。如果看到，先不要测试底盘，按 `ROS_DOMAIN_ISOLATION.md` 处理。

## 2026-06-06 混合曲线测试补充

当前平移上限为 `150 cm/s`，旋转上限为 `3.0 rad/s`，两者曲线均为 `0.1x + 0.9x³`。Motor 7 最大 `1.3 rad/s`，R2/L2 也使用同一曲线。测试顺序应为离地检查，再在安全区域逐步测试 10%/25%/50%/75%/100% 输入。START/SELECT 不再改变底盘速度。

## 2026-06-07 急停自动恢复测试

仅在底盘架空时测试。启动后监控 `ros2 topic echo /damiao_motor_status`，按下急停超过 10 秒，再释放急停且保持手柄回中。预期状态 `RECOVERING(0) -> WAIT_NEUTRAL(1) -> READY(2)`，无需重启 bash。释放急停时故意保持摇杆非零，电机必须保持零速；松杆回中后才可解锁。


## 2026-06-12 Motor 8 POS_VEL 离地测试

1. 确认 Motor 8 的 CAN ID 已设为 `8`，机构不会撞限位，急停可立即操作。
2. 重新构建并启动：

```bash
colcon build --symlink-install --packages-select base_omniwheel_r2_700 r1_arm_control
source install/setup.bash
./r1_start_base_1_0.sh
```

3. 监控：

```bash
ros2 topic echo /motor8_position_input
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

4. 先短按 R3/L3，确认正负方向和微调保持；再按一次 X，目标应从 `0.0` 变为
`0.3 rad`；再次按 X 应回到 `0.0 rad`。
5. 拔掉手柄或停止 bridge 后，Motor 8 应停止继续追赶旧目标并保持实时位置。
6. 急停恢复后，必须先收到新鲜反馈并同步当前位置，旧的 A/B 目标不得自动重放。

根据实测临时调参：

```bash
ros2 param set /motor8_position_controller_node position_b_rad 0.2
ros2 param set /motor8_position_controller_node min_position_rad -0.3
ros2 param set /motor8_position_controller_node max_position_rad 0.3
ros2 param set /motor8_position_controller_node preset_speed_rad_s 0.2
```

## 2026-06-13 Motor 8 多圈参数复测

当前源码默认值：

```text
A = 0.0 rad
B = 33.0 rad
soft limit = -32.0..32.0 rad
preset speed = 3.0 rad/s
trim speed = 2.0 rad/s
```

复测时先保持无危险负载，并依次检查：X 到 B、X 回 A、L3/R3 两端软限位、松键保持、
手柄断连保持和急停恢复。同步监控：

```bash
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

特别记录 `actual_q` 在目标超过 `12.5 rad` 后是否继续真实增长。如果反馈固定在边界，
不能依赖当前反馈完成多圈到位、断连保持或恢复同步。

## 2026-06-13 Motor 7/8 共享按键测试

1. 启动后检查 `/motor_position_selector_status`，预期 `selected_motor_id = 7`。
2. 短按 Motor 7 的 L2/R2，确认只有 Motor 7 微调；X 控制 Motor 7 A/B。
3. 松开 X/L2/R2 后按 START，预期 selected ID 变为 8。
4. 再测试 L2/R2/X，确认只有 Motor 8 动作，Motor 7 保持。
5. 按住任一 L2/R2/X 时按 START，必须保持当前选择，`switch_blocked = 1`。
6. 手柄断连时，两台电机都停止修改目标并保持实时位置。

监控：

```bash
ros2 topic echo /motor_position_selector_status
ros2 topic echo /motor7_position_status
ros2 topic echo /motor8_position_status
ros2 topic echo /damiao_motor_status
```

## 2026-06-13 Motor 7/8 三位置测试

对当前所选电机连续短按 X 三次，预期：

```text
按第1次：target_q = +32，selected_position = 1
按第2次：target_q = -32，selected_position = 2
按第3次：target_q = 0，selected_position = 0
```

切换到另一台电机后重复测试，确认两台电机的索引互不影响。测试多圈目标时保持急停可用，
并继续观察超过 `+-12.5 rad` 后的反馈是否真实可靠。


## 2026-06-13 六路 relay 与双 arm 无动力测试

先断开气源或移除危险负载，再启动系统：

```bash
ros2 topic echo /motor_position_selector_status
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

预期启动 command：

```text
/pneumatic_gripper_cmd = [0,1,0,1,1]
/kfs_staff_gripper_cmd = [0]
Arduino SENT = [0,0,1,0,1,1]
```

测试顺序：先确认默认 Motor7，按 A/B 只改变 command 第 1/2 项；松开全部按钮后按 START，
确认 selected ID=8，再按 A/B/SELECT，只应改变第 4/5/3 项。Y 始终只改变 KFS command。
停止 joystick 数据超过 0.3 s 后，arm command 应恢复 `[0,1,0,1,1]`；任一串口 command
来源停止超过 0.5 s 后，Arduino 聚合状态中该来源负责的 relay 应恢复安全值。


## 2026-06-14 手動人視角與 Motor6 測試

先架空底盤或在空曠區域低幅度測試。啟動後：

```bash
ros2 topic echo /view_orientation
ros2 topic echo /local_driving
ros2 topic echo /horizontal_speed_cmd
```

預期啟動 `/view_orientation=0`。依次測試：

1. E-stop 朝人前方，十字鍵上，左搖桿向前，`/local_driving data[0]` 約為 `0`。
2. 左搖桿回中，十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `+1.57 rad`。
3. 左搖桿回中，十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `-1.57 rad`。
4. 左搖桿回中，十字鍵下，狀態變為 `2`；左搖桿向前，方向約為 `+/-3.14 rad`。
5. 左搖桿未回中時按十字鍵，`/view_orientation` 不應改變；鬆開十字鍵及左搖桿後重按。
6. `L2` 全按預期 `/horizontal_speed_cmd` 接近 `[30.0]`。
7. `R2` 全按預期 `/horizontal_speed_cmd` 接近 `[-30.0]`。
8. 同時按 `L2+R2` 或全部鬆開，預期 `[0.0]`。

四方向確認完成後，再落地低速確認左搖桿方向與人的視角一致。沒有 IMU，車身旋轉或操作人
改變站位後必須手動重新設定十字鍵方向。

實機結果（2026-06-15）：以上人視角四方向與 Motor6 `L3/R3` 測試全部通過。

## 2026-06-16 P1／P2 背鍵 remap 測試

P1／P2 由 8BitDo 軟體設定為：

```text
P1 = R3
P2 = L3
```

啟動後監控：

```bash
ros2 topic echo /joystick_data
ros2 topic echo /pneumatic_gripper_cmd
```

預期結果：

1. 切到 STAFF mode 後按 `P1`，`/joystick_data` 應顯示 `r3: true`，`/pneumatic_gripper_cmd[3]` 應切換 Motor7 inclination/head relay。
2. 切到 STAFF mode 後按 `P2`，`/joystick_data` 應顯示 `l3: true`，`/pneumatic_gripper_cmd[1]` 應切換 Motor8 inclination/head relay。
3. 切到 KFS mode 後 P1/P2 不應控制 `/horizontal_speed_cmd`；Motor6 horizontal 由 L2/R2 控制。

注意：P1／P2 目前沒有獨立 evdev event，不應期待 `/joystick_data` 出現 `p1` 或 `p2`
欄位。這次測試確認的是背鍵作為 L3／R3 替代鍵可用。

## 2026-06-18 七路 Arduino relay 測試

只接 Arduino 和 relay board、不要先接危險負載。啟動：

```bash
ros2 run kfs_staff_gripper kfs_staff_gripper_arduino_node
ros2 topic echo /kfs_staff_gripper_status
```

啟動後預期 status 看到七路格式：

```text
SENT startup_safe_state [0,0,1,0,1,1,0]
```

再分別測 topic：

```bash
ros2 topic pub --once /kfs_staff_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [1]}"
ros2 topic pub --once /kfs_staff_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0]}"
ros2 topic pub --once /pneumatic_gripper_cmd std_msgs/msg/Int32MultiArray "{data: [0,1,0,1,1,0]}"
```

預期 Arduino Serial 回報 `Command OK`，且 `/kfs_staff_gripper_status` 中所有 `SENT` 都是
`[x,x,x,x,x,x,x]` 七個值。此測試命令最後一位為 Motor7 inclination / relay7，使用 `0` 保持低位安全狀態。

## 2026-06-18 Motor7 inclination / Relay 7 測試

在不接危險負載或先拔掉氣管的情況下測試。啟動後監控：

```bash
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

預期 `/pneumatic_gripper_cmd` 現在是 6 個值：

```text
[M7 height, M7 gripper, M8 inclination, M8 height, M8 gripper, M7 inclination]
```

測試流程：

1. START 選中 Motor7。
2. 按 SELECT，預期 `/pneumatic_gripper_cmd` 最後一位 M7 inclination 在 `0/1` 間切換。
3. START 選中 Motor8。
4. 按 SELECT，預期 `/pneumatic_gripper_cmd` 第三位 M8 inclination 在 `0/1` 間切換。
5. 觀察 `/kfs_staff_gripper_status`，預期 Arduino `SENT` 仍為七路 `[x,x,x,x,x,x,x]`。

完整安全狀態仍為：

```text
[0,0,1,0,1,1,0]
```

## 2026-06-18 Controller-gated autostart 測試

手動測試 watcher，不先安裝 systemd：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
./scripts/wait_and_start_robot.sh
```

預期：

```text
手柄未開：waiting for controller...
手柄打開：controller active; starting robot system
```

成功後確認 tmux：

```bash
tmux attach -t r1_control
```

systemd 安裝後用以下指令看狀態與 log：

```bash
systemctl status r1-control-autostart.service
journalctl -u r1-control-autostart.service -f
```

預設 `STOP_ON_CONTROLLER_LOST=0`，所以手柄中途關掉不會自動 kill `r1_control`。這是目前建議比賽配置。

## 2026-06-18 四鍵長按關機 dry-run 測試

啟動完整系統後監控：

```bash
ros2 topic echo /robot_power_status
```

測試流程：

1. 確認 `power_shutdown` tmux window 正在跑 `joystick_shutdown_node`。
2. 同時長按 `X + Y + B + A` 5 秒。
3. 預期 `/robot_power_status` 顯示 `DRY_RUN shutdown_combo_held`。
4. dry-run 模式下 Pi 不應關機，tmux session 不應被 kill。
5. 正式模式 `dry_run=false` 下，預期 `/robot_power_status` 先顯示 `SHUTDOWN combo_held`，再顯示 `SHUTDOWN_COMMAND_STARTED sudo -n /usr/bin/systemctl poweroff`，然後 Pi 關機。

目前 sudoers 已要求允許 `robotics` 免密執行 `/usr/bin/systemctl poweroff`。node 不應先 kill 自己所在的 tmux session；poweroff 命令啟動後讓 systemd 完成關機。


## 2026-06-19 KFS gripper 人視角測試覆蓋

本節取代上一段以 E-stop 為基準的預期值。現在 `/view_orientation` 表示 KFS gripper 在人視角中的方向。

啟動後預期 `/view_orientation=2`，代表 KFS gripper 在人視角後方／靠近操作人。依次測試：

1. KFS gripper 朝向操作人，保持預設或按十字鍵下，左搖桿向前，`/local_driving data[0]` 約為 `+1.57 rad`。
2. 左搖桿回中，十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `0 rad`。
3. 左搖桿回中，十字鍵上，狀態變為 `0`；左搖桿向前，方向約為 `-1.57 rad`。
4. 左搖桿回中，十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `+/-3.14 rad`。
5. 左搖桿未回中時按十字鍵，`/view_orientation` 不應改變；鬆開十字鍵及左搖桿後重按。

四方向確認完成後，再落地低速確認左搖桿方向與人的視角一致。沒有 IMU，車身旋轉或操作人改變站位後仍必須手動重新設定十字鍵方向。


## 2026-06-19 KFS gripper 車頭標測試覆蓋

本節取代同日 KFS `+1` 偏移方案的測試預期。現在 `/view_orientation` 表示 KFS gripper／車頭在人視角中的方向。

啟動後預期 `/view_orientation=2`，代表 KFS gripper／車頭在你視角後方／靠近你。依次測試：

1. KFS gripper 朝向操作人，保持預設或按十字鍵下，左搖桿向前，`/local_driving data[0]` 約為 `+/-3.14 rad`。
2. 左搖桿回中，十字鍵上，狀態變為 `0`；左搖桿向前，方向約為 `0 rad`。
3. 左搖桿回中，十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `-1.57 rad`。
4. 左搖桿回中，十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `+1.57 rad`。
5. 左搖桿未回中時按十字鍵，`/view_orientation` 不應改變；鬆開十字鍵及左搖桿後重按。

落地時用低速確認：無論 KFS 在你眼中的哪個方向，按對應十字鍵後，左搖桿應該按你的視角前後左右移動。


## 2026-06-19 KFS gripper 開機預設測試覆蓋

本節取代同日 v2.2 中啟動預設 `view=2` 的測試預期。現在啟動後預期：

```text
/view_orientation = 0
```

測試順序：

1. 不按 D-pad，左搖桿向前，`/local_driving data[0]` 約為 `0 rad`。
2. 左搖桿回中，按十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `-1.57 rad`。
3. 左搖桿回中，按十字鍵下，狀態變為 `2`；左搖桿向前，方向約為 `+/-3.14 rad`。
4. 左搖桿回中，按十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `+1.57 rad`。


## 2026-06-19 KFS 車頭標 90 度校正測試

本節取代 v2.3 的測試預期。啟動後預期 `/view_orientation=0`。

KFS gripper 在最前方時測試：

1. 不按 D-pad 或按十字鍵上，左搖桿向前，機器應在你眼中向前；`/local_driving data[0]` 約為 `+1.57 rad`。
2. 左搖桿回中，按十字鍵右，狀態變為 `1`；左搖桿向前，方向約為 `0 rad`。
3. 左搖桿回中，按十字鍵下，狀態變為 `2`；左搖桿向前，方向約為 `-1.57 rad`。
4. 左搖桿回中，按十字鍵左，狀態變為 `3`；左搖桿向前，方向約為 `+/-3.14 rad`。
5. 左搖桿未回中時按十字鍵，`/view_orientation` 不應改變。


## 2026-06-19 STAFF/KFS mode 鍵位測試

先確認 mode topic：

```bash
ros2 topic echo /operation_mode
```

預期：按 `SELECT / 中左` 後變 `1`；按 `START / 中右` 後變 `2`。

STAFF mode 測試：

```bash
ros2 topic echo /motor7_position_input
ros2 topic echo /motor8_position_input
ros2 topic echo /pneumatic_gripper_cmd
```

```text
X  -> /motor8_position_input data[0] 短暫為 1
B  -> /motor7_position_input data[0] 短暫為 1
L2 -> /motor8_position_input data[1] 為負值
R2 -> /motor7_position_input data[1] 為正值
A  -> /pneumatic_gripper_cmd 第 1 項 Motor7 height toggle
Y  -> /pneumatic_gripper_cmd 第 4 項 Motor8 height toggle
R1 -> /pneumatic_gripper_cmd 第 6 項 Motor7 inclination toggle
L1 -> /pneumatic_gripper_cmd 第 3 項 Motor8 inclination toggle
```

KFS mode 測試：

```bash
ros2 topic echo /kfs_staff_gripper_cmd
```

```text
START 切到 KFS mode 後，Y 才會切換 /kfs_staff_gripper_cmd
SELECT 切回 STAFF mode 後，Y 不應再改 /kfs_staff_gripper_cmd，而是改 Motor8 height
```

安全檢查：切 mode 時不要按其他機構鍵，確認 mode 切換本身不會讓 `/pneumatic_gripper_cmd`、`/motor7_position_input`、`/motor8_position_input` 產生動作事件。


## 2026-06-19 KFS mode Zone2 擴展測試

先切 KFS mode：

```text
按 START / 中右
/operation_mode 應為 2
```

監控：

```bash
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /horizontal_speed_cmd
ros2 topic echo /elevator_speed_cmd
```

預期：

```text
Y  -> /kfs_staff_gripper_cmd toggle
L2 -> /horizontal_speed_cmd 負值
R2 -> /horizontal_speed_cmd 正值
L1 -> /elevator_speed_cmd 負值
R1 -> /elevator_speed_cmd 正值
```

再切回 STAFF mode：

```text
按 SELECT / 中左
/operation_mode 應為 1
```

STAFF mode 下，L2/R2 應只影響 `/motor8_position_input`、`/motor7_position_input`；L1/R1 應只影響 `/pneumatic_gripper_cmd` 的 Motor8/Motor7 inclination；`/horizontal_speed_cmd` 與 `/elevator_speed_cmd` 應保持 `0.0`。


## 2026-06-19 五路 relay 測試

監控 Arduino 聚合輸出：

```bash
ros2 topic echo /pneumatic_gripper_cmd
ros2 topic echo /kfs_staff_gripper_cmd
ros2 topic echo /kfs_staff_gripper_status
```

預期 command 長度：

```text
/kfs_staff_gripper_cmd = [KFS]
/pneumatic_gripper_cmd = [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
Arduino serial = [KFS, M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

STAFF mode 測試：

```text
B  -> /pneumatic_gripper_cmd 第 1 項 toggle，並觸發 /motor7_position_input toggle
X  -> /pneumatic_gripper_cmd 第 3 項 toggle，並觸發 /motor8_position_input toggle
R1 -> /pneumatic_gripper_cmd 第 4 項 toggle
L1 -> /pneumatic_gripper_cmd 第 2 項 toggle
A  -> 不應改 /pneumatic_gripper_cmd
Y  -> STAFF mode 不應改 /pneumatic_gripper_cmd，也不應改 /kfs_staff_gripper_cmd
```

KFS mode 測試：

```text
Y -> /kfs_staff_gripper_cmd toggle
```


## 2026-06-19 STAFF/KFS 最新鍵位測試

STAFF mode (`SELECT / 中左`)：

```bash
ros2 topic echo /motor7_position_input
ros2 topic echo /motor8_position_input
ros2 topic echo /pneumatic_gripper_cmd
```

預期：

```text
Y  -> /motor7_position_input data[0] 短暫為 1；/pneumatic_gripper_cmd 第 1 項 toggle
A  -> /motor8_position_input data[0] 短暫為 1；/pneumatic_gripper_cmd 第 3 項 toggle
R1 -> /motor7_position_input data[1] 負值
R2 -> /motor7_position_input data[1] 正值
L1 -> /motor8_position_input data[1] 負值
L2 -> /motor8_position_input data[1] 正值
B/X -> 不應改 /motor7_position_input、/motor8_position_input 或 /pneumatic_gripper_cmd
```

KFS mode (`START / 中右`)：

```bash
ros2 topic echo /horizontal_speed_cmd
```

```text
L2 -> /horizontal_speed_cmd 正值
R2 -> /horizontal_speed_cmd 負值
```


## 2026-06-19 STAFF mode L3/R3 抬頭測試

STAFF mode (`SELECT / 中左`) 下監控：

```bash
ros2 topic echo /pneumatic_gripper_cmd
```

五路 pneumatic command 的四路 arm 部分為：

```text
[M7 gripper, M8 inclination, M8 gripper, M7 inclination]
```

預期：

```text
L3 -> 第 2 項 Motor8 inclination toggle
R3 -> 第 4 項 Motor7 inclination toggle
```


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


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。

## 2026-06-20 KFS mechanism speed parameters

目前 source code 中 KFS mode 的機構速度如下：

```text
Motor5 elevator = 28.0 rad/s
  L1: negative/down
  R1: positive/up

Motor6 horizontal = 30.0 rad/s
  L2: positive/out at full trigger
  R2: negative/in at full trigger
```

對應參數：`elevator_joystick_bridge_node.command_speed_rad_s=28.0`、`elevator_controller_node.max_speed_rad_s=28.0`、`horizontal_joystick_bridge_node.command_speed_rad_s=30.0`、`horizontal_controller_node.max_speed_rad_s=30.0`。只有 `/operation_mode=2` 時生效；超時保護仍為 `timeout_sec=0.3 s`。

## 2026-06-20 STAFF D-pad Down Motor7/Motor8 Swap

目前 STAFF mode 會讀取 `/view_orientation`。規則：

```text
/view_orientation = 0  # D-pad 上，KFS visual front 在機手前方
  STAFF mapping 保持正常：Motor7 按鍵仍控制 Motor7，Motor8 按鍵仍控制 Motor8

/view_orientation = 2  # D-pad 下，KFS visual front 在機手後方
  STAFF mapping 對調：所有 Motor7 staff gripper 控制改送 Motor8，所有 Motor8 staff gripper 控制改送 Motor7
```

D-pad 左/右 (`1/3`) 目前不觸發對調，保持正常 mapping。對調只在 STAFF mode (`/operation_mode=1`) 影響 staff gripper 相關控制；KFS mode、底盤左/右搖桿、Motor5 elevator、Motor6 horizontal 不受影響。

正常 mapping：

```text
A -> Motor7 90° / preset
X -> Motor8 90° / preset
B -> Motor7 staff gripper relay
Y -> Motor8 staff gripper relay
R1/R2 -> Motor7 trim -/+
L1/L2 -> Motor8 trim -/+
R3/P1 -> Motor7 inclination/head relay
L3/P2 -> Motor8 inclination/head relay
```

D-pad 下 swap mapping：

```text
A -> Motor8 90° / preset
X -> Motor7 90° / preset
B -> Motor8 staff gripper relay
Y -> Motor7 staff gripper relay
R1/R2 -> Motor8 trim +/-   # R1/R2 also swapped, so R1 positive and R2 negative
L1/L2 -> Motor7 trim +/-   # L1/L2 also swapped, so L1 positive and L2 negative
R3/P1 -> Motor8 inclination/head relay
L3/P2 -> Motor7 inclination/head relay
```

相關參數：

```text
motor_position_selector_joystick_bridge_node.swap_staff_grippers_on_view_down = true
pneumatic_gripper_joystick_bridge_node.swap_staff_grippers_on_view_down = true
```

## 2026-06-20 Chassis Rotation Speed

Right stick rotation speed default is now:

```text
joystick_bridge.max_rotation = 3.0 rad/s
```

The rotation curve remains:

```text
rotation = (0.1x + 0.9x^3) * max_rotation
```

So small right-stick input still gives fine control, while full right-stick input can request up to `3.0 rad/s`. Actual chassis motion may still be scaled by `local_navigation_node.max_wheel_speed_rad_s = 40.0 rad/s` when translation and rotation are combined.

### 2026-06-20 STAFF D-pad Down Trim Direction Update

D-pad 下的 STAFF swap 現在也會把微調方向一起對調：`R1/R2` 互換、`L1/L2` 互換。因此 D-pad 下時：

```text
R1 -> Motor8 trim positive
R2 -> Motor8 trim negative
L1 -> Motor7 trim positive
L2 -> Motor7 trim negative
```

D-pad 上仍保持原本：`R1/R2=Motor7 -/+`，`L1/L2=Motor8 -/+`。

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
