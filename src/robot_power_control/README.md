> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

> 2026-06-19 現行操作準則：手柄鍵位、STAFF/KFS mode、D-pad 視角與五路 relay 順序以 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md` 為唯一準則。本文件較早日期的鍵位段落保留為歷史紀錄，不作為目前實機操作依據。

# robot_power_control

## Changelog

### 2026-06-18 v0.1.0 joystick shutdown dry-run

- 新增 `joystick_shutdown_node`。
- 預設使用 `X + Y + B + A` 同時長按 `5.0 s` 觸發。
- 預設 `dry_run=true`，只發布狀態，不會真的關機。
- 新增 `/robot_power_status` 方便測試與監控。

## Package 用途

`robot_power_control` 是機器人電源管理 package。它不控制 arm、底盤、氣動或 joystick driver，只負責把 operator 的明確關機意圖轉成系統關機流程。

此 package 不綁定某一年比賽流程；按鍵、長按時間、shutdown command 和 tmux session 都可用參數調整。

## Nodes

### joystick_shutdown_node

職責：訂閱 joystick topic，偵測可配置按鍵組合是否連續長按足夠時間，然後進入 dry-run 或執行 shutdown command。

#### Subscribe

| Topic | Type | 說明 |
|---|---|---|
| `/joystick_data` | `my_joystick_msgs/msg/Joystick` | 手柄按鍵狀態，預設使用 `x/y/b/a` |

#### Publish

| Topic | Type | 說明 |
|---|---|---|
| `/robot_power_status` | `std_msgs/msg/String` | `READY`、`DRY_RUN`、`SHUTDOWN`、`RESET input_timeout` 等狀態 |

#### Parameters

| Parameter | Default | Unit | 說明 |
|---|---:|---|---|
| `joystick_topic` | `/joystick_data` | - | joystick input topic |
| `status_topic` | `/robot_power_status` | - | status output topic |
| `required_buttons` | `['x','y','b','a']` | - | 必須同時按住的按鍵欄位 |
| `hold_sec` | `5.0` | s | 持續按住多久才觸發 |
| `input_timeout_sec` | `0.5` | s | joystick topic 超時後清空長按計時 |
| `watchdog_hz` | `10.0` | Hz | timeout 檢查頻率 |
| `dry_run` | `true` | - | true 時只 log/status，不執行關機 |
| `stop_tmux_before_shutdown` | `false` | - | poweroff 命令啟動後是否額外 kill tmux session |
| `stop_tmux_session` | `r1_control` | - | 要停止的 tmux session 名稱 |
| `shutdown_command` | `sudo -n /usr/bin/systemctl poweroff` | - | dry_run=false 時執行的命令，`-n` 避免卡密碼提示 |

## Timeout / Watchdog

`joystick_shutdown_node` 有 ROS 側 input watchdog：

```text
條件：超過 input_timeout_sec 沒有收到 /joystick_data
預設：0.5 s
行為：清空目前長按計時，發布 RESET input_timeout
```

這能避免手柄斷線時保留半完成的長按狀態。

## 最小可運行示例

安全 dry-run 測試：

```bash
ros2 run robot_power_control joystick_shutdown_node --ros-args -p dry_run:=true
ros2 topic echo /robot_power_status
```

同時長按 `X + Y + B + A` 5 秒，預期看到：

```text
DRY_RUN shutdown_combo_held
```

正式關機前需要允許 `robotics` 執行 poweroff，例如用 sudoers 精確授權：

```text
robotics ALL=NOPASSWD: /usr/bin/systemctl poweroff
```

然後才改：

```bash
ros2 run robot_power_control joystick_shutdown_node --ros-args -p dry_run:=false
```

## 調試方式

```bash
ros2 topic echo /joystick_data
ros2 topic echo /robot_power_status
ros2 param get /joystick_shutdown_node dry_run
ros2 param get /joystick_shutdown_node hold_sec
```

## 常見問題

- 長按沒有觸發：確認 `/joystick_data` 中 `x/y/b/a` 都變成 `true`。
- 觸發但沒有關機：確認 `dry_run=false`，確認 sudoers 允許 `/usr/bin/systemctl poweroff`，並確認 `shutdown_command` 是 `sudo -n /usr/bin/systemctl poweroff`。
- 誤觸風險：把 `hold_sec` 調大，或修改 `required_buttons`。


## 2026-06-19 現行手柄鍵位總表（以 CONTROLLER_USAGE.md 為準）

目前手柄操作的唯一準則已整理到 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。若本文件前面存在舊版鍵位描述，保留為歷史紀錄；實機操作以本節和 `CONTROLLER_USAGE.md` 為準。

固定不變：左搖桿控制底盤平移，右搖桿控制底盤旋轉，D-pad 設定 KFS visual front 的人視角方向，`X+Y+B+A` 長按 5 秒觸發 Raspberry Pi shutdown command。

模式切換：`SELECT/中左 = STAFF mode (/operation_mode=1)`，`START/中右 = KFS mode (/operation_mode=2)`。

STAFF mode：`A=Motor7 左右 90°/preset`，`X=Motor8 左右 90°/preset`，`B=Motor7 staff gripper relay`，`Y=Motor8 staff gripper relay`，`R1/R2=Motor7 微調 -/+`，`L1/L2=Motor8 微調 -/+`，`R3/P1=Motor7 抬頭/inclination relay`，`L3/P2=Motor8 抬頭/inclination relay`。

KFS mode：`Y=KFS gripper`，`L2/R2=Motor6 horizontal positive/negative`，`L1/R1=Motor5 elevator negative/positive`。

最新 Arduino 五路 relay 順序為 `[KFS gripper, M7 gripper, M8 inclination, M8 gripper, M7 inclination]`，安全狀態為 `[0,1,0,1,0]`。


## 2026-06-19 手柄四鍵長按 shutdown

`joystick_shutdown_node` 監聽 `/joystick_data`，當 `X+Y+B+A` 同時長按 `hold_seconds=5.0` 時發布 `/robot_power_status` 並執行關機命令。此功能不受 `/operation_mode` 影響，因為它屬於全機安全/電源控制。

若 `dry_run=true`，只發布狀態不執行 `sudo /sbin/shutdown -h now`；正式比賽使用前需要確認 sudoers 權限與 `dry_run` 參數。

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

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
