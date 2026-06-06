# Robocon R1 ROS 2 工作區

[English](README.md) | [简体中文](README.zh-CN.md) | 繁體中文

本倉庫是 EdUHK Robotics Team @ Hero 開發的目前 R1 機器人控制工作區。

- GitHub：`herolch07`
- 目前最終操作指南：[r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md)
- 系統架構說明：[ARCHITECTURE.md](ARCHITECTURE.md)
- Node/topic 圖：[NODE_GRAPH.md](NODE_GRAPH.md)
- 底盤速度調參說明：[SPEED_TUNING.md](SPEED_TUNING.md)
- 目前完整啟動腳本：`./r1_start_base_1_0.sh`
- 專案記錄中的目前實機確認日期：2026-05-22

## 目前系統

這個工作區是 Robocon R1 的 ROS 2 控制系統，包含：

- Motor 1-4：四輪全向底盤
- Motor 5：升降執行機構
- Motor 6：水平移動執行機構
- Motor 7：機械夾爪馬達
- Arduino pneumatic gripper：氣動夾爪開合與高度高/低
- 8BitDo 手掣輸入，底層使用 Linux `evdev`
- 可選鍵盤遙控 package，用於低速調試

## 手掣映射

```text
左搖桿上/下：底盤前進/後退
左搖桿左/右：底盤左/右橫移
右搖桿左/右：底盤原地旋轉
R2 / L2：Motor 5 升降正/反向
D-pad 左/右：Motor 6 水平移動
D-pad 上/下：Motor 6 水平移動速度檔位 0.2 / 0.5 / 1.0
START / SELECT：目前不用于底盤調速
R1 / L1：Motor 7 機械夾爪正/反向
B：按住 arm pneumatic gripper OPEN，放開 CLOSE
A：arm pneumatic height LOW 鎖定
X：arm pneumatic height HIGH 鎖定
Y：KFS staff gripper OPEN，放開 CLOSE
R3：目前不使用
```

## 目前重要預設值

```text
手掣搖桿範圍：-512 .. 512
扳機範圍：0 .. 512
手掣死區：24
joystick_bridge max_speed_cm：150.0
joystick_bridge max_rotation：0.5
joystick_bridge translation_linear_weight：0.2
local_navigation_node max_wheel_speed_rad_s：64.0
joystick_bridge input_timeout_sec：0.3
local_navigation_node command_timeout_sec：0.3
damiao_node command_timeout_sec：0.5
pneumatic safe_state：[0, 1] = LOW + CLOSE
```

底盤運動學預設值：

```text
Motor 1 = 左前
Motor 2 = 右前
Motor 3 = 右後
Motor 4 = 左後

lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4 = [1, 1, -1, -1]
lateral_coeff_1..4 = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

## 快速啟動

在機器人主機上執行：

```bash
cd /home/robotics/robocon/new_ws
colcon build --symlink-install
source install/setup.bash
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

腳本會啟動 tmux session：

```text
r1_control
```

常用 tmux 命令：

```text
重新進入：tmux attach -t r1_control
離開但保持運行：Ctrl+b，然後按 d
關閉全部：tmux kill-session -t r1_control
```

## Package 一覽

```text
src/my_joystick_msgs          自訂 Joystick 訊息
src/my_joystick_driver        evdev 手掣驅動，發布 /joystick_data
src/joystick_bridge           手掣到底盤 /local_driving 的橋接
src/base_omniwheel_r2_700     全向底盤運動學與達妙馬達驅動
src/r1_arm_control            Motor 5/6/7 速度控制與手掣橋接
src/kfs_staff_gripper       KFS/arm pneumatic 三路 Arduino relay aggregator
src/arduino_pneumatic_driver  Arduino relay 氣動夾爪 joystick bridge
src/keyboard_teleop           鍵盤低速調試遙控
```

## 安全保護

目前控制鏈有多層 watchdog：

- `joystick_bridge`：`/joystick_data` 超時後發布 `/local_driving = [0, 0, 0]`。
- `local_navigation_node`：`/local_driving` 超時後讓 Motor 1-4 歸零。
- `damiao_node`：連續 VEL 命令超時後只讓對應馬達歸零。
- `r1_arm_control` controllers：對應 speed command 超時後執行機構速度歸零。
- `arduino_pneumatic_driver`：命令超時、重連、關閉時發送 `safe_state = [0, 1]`。

## 舊文件說明

本工作區裡有一些歷史報告。如果某段內容提到 `±8192`、`410` 手掣死區、`100 cm/s` 預設底盤速度、`start_all_nodes.sh`、`start_full_control_chain.sh`、VESC 節點，或舊路徑 `Robocon2026_r2/2026R2_ws`，除非該段明確標成目前狀態，否則應視為舊版記錄。

目前操作以本 README 和 [r1 final operation guide 1.0.md](r1%20final%20operation%20guide%201.0.md) 為準。

## ROS2 網絡隔離

R1 啟動腳本預設使用獨立 ROS2 環境：

```bash
ROS_DOMAIN_ID=1
ROS_LOCALHOST_ONLY=1
```

這樣可以避免 R1 發現 R2 的 `/damiao_motor_controller`、`/global_navigation_node`、`/base/dummy_control` 等 node/topic。修改前請先閱讀 `ROS_DOMAIN_ISOLATION.md`。
