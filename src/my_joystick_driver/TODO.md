> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# Joystick Driver 开发任务清单

## v1.0 基础功能（初始版本）
- [x] 基础手柄驱动实现（使用 evdev 库读取 Linux 输入事件）
- [x] 消息定义（Joystick.msg）
- [x] 自动设备检测（扫描 /dev/input/event*）
- [x] 定时发布机制（20Hz 固定频率）
- [x] 基础按键和摇杆映射
- [x] 蓝牙/USB 连接支持

## v2.0 增强功能（2026-01-29 完成，当前已按 R1 实机版本调整）
- [x] 数据归一化已按 R1 实机控制更新为 ±512（trigger 为 0~512）
- [x] 死区过滤实现；2026-06-07 从 24 调整为 15（约 2.93%）
- [x] 断线自动归零保护
- [x] ROS2 参数化配置系统
  - [x] auto_detect 参数（自动检测开关）
  - [x] device_path 参数（手动指定设备路径）
  - [x] device_name_filter 参数（设备名称过滤器）
- [x] 详细设备调试信息（连接失败时打印所有可用设备）
- [x] 多品牌手柄支持（8BitDo, Xbox, PS5 等）
- [x] 完整 README 文档
  - [x] ROS2 接口参考章节
  - [x] 蓝牙连接教程
  - [x] 完整故障排查流程
  - [x] 升级说明对比

## v2.1 规范化改进（当前进行中）
- [x] 添加 TODO.md（符合 AGENTS.md 规范）
- [x] README 添加 Changelog 章节
- [x] 超时保护机制文档化
- [x] 声明并记录 `python3-evdev` / `evdev` 运行依赖（2026-06-10）
- [ ] 单元测试（基础功能覆盖）
- [ ] CI/CD 集成

## 待完成功能
- [ ] 按键映射可配置化（通过 YAML 参数文件）
- [ ] 多手柄同时支持（发布到不同 namespace）
- [ ] 手柄振动反馈功能（力反馈支持）
- [ ] QoS Deadline 超时检测（订阅端看门狗）
- [ ] 电池电量监测（如果手柄支持）
- [ ] 手柄固件版本检测
- [ ] 性能监控（发布延迟统计）

## 已知问题
- [ ] 某些 Xbox 手柄的扳机初始值为 -32768（需要特殊处理）
- [ ] D-pad 在某些手柄上映射不一致
- [ ] 蓝牙连接断开后，有时需要手动重新配对

## 优化计划
- [ ] 减少 CPU 占用（优化事件循环）
- [ ] 支持动态调整发布频率
- [ ] 添加手柄校准工具
- [ ] 支持自定义按键宏（组合键）

## 2026-06-11 8BitDo 主/后备手柄白名单

- [x] 记录旧 Ultimate 2.4G 的 `2dc8:3106` 与 evdev 名称
- [x] 记录新 Ultimate 3-mode Xbox 的 `2dc8:200f` 与 evdev 名称
- [x] 将两个实机确认名称加入自动检测白名单
- [x] 保留 `device_name_filter` 对其他手柄的手动匹配能力
- [x] 保持现有 ABXY/摇杆映射不变
- [x] 新增白名单与误匹配单元测试
- [ ] 新手柄需要使用 L2/R2 时，改为动态读取 `AbsInfo` 轴范围
- [ ] 分别实机确认两只手柄启动 bash 后可自动连接并发布 `/joystick_data`

## 2026-06-16 8BitDo P1／P2 背鍵確認

- [x] 使用 `evtest` 確認 A/B/X/Y 有事件
- [x] 確認 P1／P2 目前沒有獨立 evdev event
- [x] 決定不修改 `Joystick.msg` 或 `joystick_node.py`
- [x] 記錄目前手柄 remap：`P1 = R3`、`P2 = L3`
- [ ] 若未來切換模式後 P1／P2 有獨立 `EV_KEY` code，再新增 `p1/p2` 欄位


## 2026-06-19 P1/P2 現行用途

- [x] 保持 P1/P2 不新增獨立 ROS 欄位
- [x] 記錄目前 remap：`P1=R3`、`P2=L3`
- [x] 記錄現行用途：STAFF mode `P1/R3=Motor7 inclination`、`P2/L3=Motor8 inclination`
- [ ] 若未來手柄模式能提供獨立 P1/P2 evdev code，再評估擴充 message

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
