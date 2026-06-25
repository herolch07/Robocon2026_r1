# EdUHK Robocon R1 ROS 2 Workspace

本仓库是 EdUHK Robocon Robotics Team 的 R1 机器人 ROS 2 控制工作区。当前版本以手柄控制为主，覆盖底盘、达妙电机、STAFF gripper、KFS gripper、Arduino 五路继电器气动面板、自动启动与安全 watchdog。

维护者：Hero@EdUHK Robotics Team 2026  
GitHub：`herolch07`

## 当前状态

这是 R1 控制系统的当前最终整理版 README。打开 GitHub 仓库时应优先阅读本文件。

当前正式操作与接口以以下文件为准：

- [QUICK_START.md](QUICK_START.md)：最快启动和验证步骤
- [CONTROLLER_USAGE.md](CONTROLLER_USAGE.md)：当前手柄按键表
- [ARCHITECTURE.md](ARCHITECTURE.md)：系统架构和节点职责
- [NODE_GRAPH.md](NODE_GRAPH.md)：node/topic 数据流
- [TESTING_GUIDE.md](TESTING_GUIDE.md)：测试与实机检查
- [SAFETY_REPORT.md](SAFETY_REPORT.md)：安全机制说明

历史文档和早期调参记录只用于回溯，不再作为当前实机操作依据。
本次清理前的旧版根目录 README 已归档到 [docs/history/README.root-before-cleanup.md](docs/history/README.root-before-cleanup.md)。

## 命名说明

当前正确名称是 **STAFF gripper**，不是 arm gripper。

仓库里仍可能出现以下旧命名：

- `arm_gripper_controller_node`
- `arm_gripper_joystick_bridge_node`
- `/arm_gripper_speed_cmd`
- `/arm_gripper_status`

这些属于旧的 Motor 7 速度控制链路，当前正式启动脚本不再使用。当前 STAFF gripper 由以下链路控制：

- Motor 7 / Motor 8 位置控制：`motor7_position_controller_node`、`motor8_position_controller_node`
- STAFF pneumatic relay：`pneumatic_gripper_joystick_bridge_node`
- Arduino 五路 relay 聚合：`kfs_staff_gripper_arduino_node`

如果后续要重命名目录或 package，建议不要直接把 `src/r1_arm_control` 改名为 `staff_gripper_control`，因为这个 package 还包含 Motor 5 elevator、Motor 6 horizontal、Motor 7/8 position，不只负责 STAFF gripper。更合理的做法是：

```text
src/r1_arm_control -> src/r1_mechanism_control
package name       -> r1_mechanism_control
```

如果只想修正旧 gripper 命名，可以逐步把旧节点改为 legacy 或删除，而不是让 package 名称只代表其中一个机构。

## 当前系统组成

```text
Motor 1-4  : 四轮全向底盘，VEL 模式
Motor 5    : KFS elevator，VEL 模式
Motor 6    : KFS horizontal，VEL 模式
Motor 7    : STAFF gripper position motor，POS_VEL 模式
Motor 8    : STAFF gripper position motor，POS_VEL 模式
Arduino    : 五路 relay 面板，控制 KFS gripper、Motor7/8 STAFF gripper relay、Motor7/8 head/inclination relay
Controller : 8BitDo 手柄，通过 Linux evdev 输入
```

## 快速启动

在机器人主机上：

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
colcon build --symlink-install
source install/setup.bash
chmod +x r1_start_base_1_0.sh
./r1_start_base_1_0.sh
```

启动后会创建 tmux session：

```text
r1_control
```

常用 tmux 操作：

```text
进入窗口: tmux attach -t r1_control
离开窗口: Ctrl+b, then d
停止系统: tmux kill-session -t r1_control
```

## 当前启动节点

`r1_start_base_1_0.sh` 是当前正式启动脚本，会启动：

```text
joystick_node
operation_mode_selector_node
joystick_bridge
damiao_node
local_navigation_node
elevator_controller_node
elevator_joystick_bridge_node
horizontal_controller_node
horizontal_joystick_bridge_node
motor7_position_controller_node
motor8_position_controller_node
motor_position_selector_joystick_bridge_node
kfs_staff_gripper_arduino_node
pneumatic_gripper_joystick_bridge_node
kfs_staff_gripper_joystick_bridge_node
joystick_shutdown_node
monitor shell
```

不要把旧的 `start.sh`、`start_background.sh`、`start_ssh.sh` 当作当前正式入口。

## 手柄按键

固定功能：

```text
左摇杆: 底盘平移，按操作者视角控制
右摇杆: 底盘原地旋转
D-pad : 设置 KFS visual front 在操作者视角中的方向
X + Y + B + A 长按 5 秒: Raspberry Pi shutdown
```

模式选择：

```text
SELECT / 中左: STAFF mode (/operation_mode = 1)
START  / 中右: KFS mode   (/operation_mode = 2)
```

STAFF mode：

```text
A     : Motor7 STAFF gripper 90-degree / preset cycle
X     : Motor8 STAFF gripper 90-degree / preset cycle
B     : Motor7 STAFF gripper relay toggle
Y     : Motor8 STAFF gripper relay toggle
R1/R2 : Motor7 trim negative / positive
L1/L2 : Motor8 trim negative / positive
R3/P1 : Motor7 head / inclination relay toggle
L3/P2 : Motor8 head / inclination relay toggle
```

KFS mode：

```text
Y     : KFS gripper toggle
L2/R2 : Motor6 horizontal positive(out) / negative(in)
L1/R1 : Motor5 elevator negative(down) / positive(up)
```

D-pad down 时，STAFF mode 会交换 Motor7/Motor8 的 STAFF gripper 控制映射，以适配操作者反向面对机器人时的操作直觉。详细规则见 [CONTROLLER_USAGE.md](CONTROLLER_USAGE.md)。

## 当前重要参数

```text
Joystick axis range: -512 .. 512
Trigger range: 0 .. 512
Joystick deadzone: 15

joystick_bridge.max_speed_cm: 150.0
joystick_bridge.max_rotation: 3.0
joystick_bridge.translation_linear_weight: 0.1
joystick_bridge.rotation_linear_weight: 0.1

local_navigation_node.max_wheel_speed_rad_s: 40.0
local_navigation_node.max_wheel_accel_rad_s2: 25.0
local_navigation_node.accel_limit_mode: per_wheel

damiao_node.motor_ids: [1,2,3,4,5,6,7,8]
damiao_node.position_mode_motor_ids: [7,8]
damiao_node.command_timeout_sec: 0.5

Motor5 elevator speed: 28.0 rad/s
Motor6 horizontal speed: 30.0 rad/s
Motor7/Motor8 position presets: [0.0, 32.0, -32.0] rad

STAFF pneumatic safe_state: [1,0,1,0]
Arduino five-relay safe_state: [0,1,0,1,0]
```

底盘当前标定：

```text
Motor 1 = left front
Motor 2 = right front
Motor 3 = right rear
Motor 4 = left rear

lateral_axis_sign = 1.0
rotation_axis_sign = 1.0
forward_coeff_1..4  = [1, 1, -1, -1]
lateral_coeff_1..4  = [1, -1, -1, 1]
rotation_coeff_1..4 = [1, -1, 1, -1]
motor_direction_1..4 = [-1, 1, -1, 1]
```

## Package 地图

```text
src/my_joystick_msgs          自定义 Joystick message
src/my_joystick_driver        evdev 手柄驱动，发布 /joystick_data
src/joystick_bridge           手柄到底盘 /local_driving 的桥接
src/base_omniwheel_r2_700     四轮全向底盘运动学与达妙电机驱动
src/operation_mode_control    STAFF/KFS 模式选择
src/r1_arm_control            当前实际是 R1 mechanism control，含 Motor5/6/7/8 控制
src/arduino_pneumatic_driver  STAFF pneumatic bridge，发布 /pneumatic_gripper_cmd
src/kfs_staff_gripper         五路 Arduino relay 聚合与 KFS gripper bridge
src/keyboard_teleop           键盘调试入口，非当前正式比赛入口
src/robot_power_control       手柄长按关机
```

## 安全机制

当前系统有多层 timeout/watchdog：

- `joystick_bridge`：`/joystick_data` 超时后发布 `/local_driving = [0,0,0]`。
- `local_navigation_node`：`/local_driving` 超时后向 Motor 1-4 发布零速度。
- `damiao_node`：电机命令超时后发零速度；反馈丢失或电机 disabled 后进入 recovery；恢复后必须收到 neutral command 才允许非零输出。
- `r1_arm_control`：Motor5/6 速度控制超时归零；Motor7/8 POS_VEL 输入超时后停止 trim 并 hold 当前反馈位置。
- `operation_mode_control`：手柄输入超时后发布 `MODE_INVALID`，下游 mechanism bridge 停止接受旧按键状态。
- `kfs_staff_gripper_arduino_node`：Arduino 串口启动、重连、关闭和命令源超时时写入 safe state。
- `robot_power_control`：`X+Y+B+A` 长按触发关机，默认节点支持 dry-run；正式启动脚本当前传入 `dry_run:=false`。

## 自动启动

仓库包含 systemd watcher：

```text
systemd/r1-control-autostart.service
scripts/wait_and_start_robot.sh
```

它会等待 8BitDo / Xbox 手柄出现后再启动 `r1_start_base_1_0.sh`。当前 `STOP_ON_CONTROLLER_LOST=0`，手柄短暂断连不会杀掉 tmux session，安全输出由各节点 watchdog 负责。

## 清理建议

如果要整理 GitHub record：

- 保留本 `README.md` 作为唯一入口说明。
- 保留每个 package 的 `README.md` 和 `TODO.md`，这是工程文档的一部分。
- 可将旧操作文档、旧启动脚本、实机 debug 脚本移到 `docs/history/` 或 `tools/hardware_debug/`。
- 建议从 Git 移除 `logs/*.log`，并在 `.gitignore` 中加入 `logs/`。
- 建议修正 `base_omniwheel_r2_700/setup.py` 中不存在的旧 console script。
- 建议给 `src/my_joystick_msgs` 补 `README.md`。

## 目录重命名建议

如果只是改显示文档，当前 README 已经把 `arm gripper` 纠正为 `STAFF gripper`。

如果要真正改目录或 package 名，需要同步修改：

```text
目录名
package.xml 的 <name>
setup.py 的 package_name
setup.cfg 的 script_dir / install_scripts
Python import 路径
console_scripts
所有 ros2 run 命令
所有文档和测试 import
```

推荐重命名路线：

```text
src/r1_arm_control
  -> src/r1_mechanism_control

r1_arm_control package
  -> r1_mechanism_control
```

不推荐把整个 `r1_arm_control` 改成 `staff_gripper_control`，因为它还负责 KFS elevator 和 KFS horizontal。若以后要进一步拆包，可以拆成：

```text
src/r1_kfs_mechanism_control
src/staff_gripper_control
```

但当前系统已经完结，最稳妥的做法是先只清理文档和旧脚本，不大规模改 ROS package 名。
