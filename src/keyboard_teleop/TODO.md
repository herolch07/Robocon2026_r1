> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# keyboard_teleop TODO

## 已完成

- [x] 新增独立 `keyboard_teleop` package，避免放入机械臂或底盘底层 package
- [x] 新增 `keyboard_teleop_node`
- [x] 支持发布底盘、升降、水平、机械夹爪、气动夹爪 command topics
- [x] 实现 `key_hold_sec` 按键输入失效保护
- [x] 实现 `SPACE` 停止和节点退出停止
- [x] README 记录 topic、参数、启动方式、超时保护和调试方式

## 待办

- [ ] 在机器人 Linux 主机上执行 `colcon build --symlink-install --packages-select keyboard_teleop`
- [ ] 实机低速测试底盘方向是否符合键盘直觉
- [ ] 根据实机测试结果调整默认速度参数
- [ ] 如需要长期使用，补充 launch 文件统一启动 keyboard teleop 测试系统

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
