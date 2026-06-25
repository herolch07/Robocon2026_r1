> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# Joystick Messages TODO

## v1.0 基础消息定义
- [x] 定义 Joystick.msg 消息格式
- [x] 包含 8 个模拟轴（lx, ly, rx, ry, dx, dy, l2, r2）
- [x] 包含 10 个数字按键（a, b, x, y, l1, r1, l3, r3, select, start）
- [x] CMakeLists.txt 配置
- [x] package.xml 依赖配置

## v2.0 数据类型优化（2026-01-29 完成，当前已按 R1 实机版本调整）
- [x] 摇杆数据类型从 int32 原始值改为归一化 int32
- [x] 数值范围已按 R1 实机控制更新为 ±512（摇杆）和 0~512（扳机）
- [x] 更新消息注释说明数值范围

## 待完成
- [ ] 添加时间戳字段（用于延迟检测）
- [ ] 添加手柄 ID 字段（用于多手柄区分）
- [ ] 添加电池电量字段（如果支持）
- [ ] 考虑添加陀螺仪/加速度计数据（部分手柄支持）

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
