> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# 系统改进建议 - 符合 AGENTS.md 规范

> 当前状态说明：本文件前半部分是 2026-02 期间的历史改进计划，其中 `timeout_sec = 0.5`、`joystick_bridge` 缺少 watchdog 等段落已不是当前代码状态。当前状态以文末“2026-05-22 当前状态更新”和根目录 `README.md` 为准。

## 📋 当前状态分析

### ✅ 已符合的规范

1. **使用 Python 实现（9.3）**
   - ✅ joystick_node.py - Python
   - ✅ joystick_bridge.py - Python
   - ✅ local_navigation_node.py - Python

2. **包含完整注释（9.3）**
   - ✅ 文件级注释说明用途
   - ✅ 类/函数级注释
   - ✅ 关键逻辑注释

3. **参数化配置（2.2.4）**
   - ✅ max_speed_cm 可配置
   - ✅ max_rotation 可配置
   - ✅ deadzone 可配置

4. **节点解耦（1）**
   - ✅ 通过 topic 通信
   - ✅ 接口清晰
   - ✅ 可独立测试

---

## ⚠️ 需要改进的部分

### 1. **缺少话题超时检测（违反 9.1）**

**AGENTS.md 要求：**
> 所有涉及控制、执行、硬件交互或关键数据链路的 node：
> - 必须实现超时保护逻辑（timeout / watchdog）

**当前问题：**
- `joystick_bridge.py` 缺少 joystick_data 话题的超时检测
- 如果 joystick_node 崩溃，bridge 会保持最后收到的指令

**建议改进：**
在 `joystick_bridge.py` 中添加看门狗定时器

```python
class JoystickBridge(Node):
    def __init__(self):
        # ... 现有代码 ...
        
        # 添加超时检测（符合 AGENTS.md 9.1）
        self.last_msg_time = self.get_clock().now()
        self.declare_parameter('timeout_sec', 0.5)  # 500ms 超时
        self.timeout_threshold = self.get_parameter('timeout_sec').get_parameter_value().double_value
        
        # 看门狗定时器
        self.watchdog_timer = self.create_timer(0.1, self.check_timeout)
        
        self.get_logger().info(f"Timeout threshold: {self.timeout_threshold}s")
    
    def joystick_callback(self, msg):
        # 更新最后收到消息的时间
        self.last_msg_time = self.get_clock().now()
        
        # ... 原有逻辑 ...
    
    def check_timeout(self):
        """检查是否超时，如果超时则发送停止指令"""
        time_since_last = (self.get_clock().now() - self.last_msg_time).nanoseconds / 1e9
        
        if time_since_last > self.timeout_threshold:
            # 发送停止指令
            stop_msg = Float32MultiArray()
            stop_msg.data = [0.0, 0.0, 0.0]
            self.nav_pub.publish(stop_msg)
            
            # 只在第一次超时时打印警告
            if time_since_last < self.timeout_threshold + 0.2:
                self.get_logger().warn(
                    f"Joystick timeout ({time_since_last:.2f}s) - sending stop command"
                )
```

**改进后的安全性：**
- ✅ 即使 joystick_node 崩溃，500ms 后会自动停止
- ✅ 符合 AGENTS.md 9.1 规范
- ✅ 增加了额外的安全保护层

---

### 2. **README.md 需要补充超时说明（违反 9.1）**

**AGENTS.md 要求：**
> 实现细节必须在该 package 的 README.md 中明确说明：
> - 超时触发条件
> - 默认超时参数及其单位
> - 超时后的系统行为
> - 如何通过参数修改超时策略

**当前问题：**
- 各 package 的 README.md 中未详细说明超时机制
- SAFETY_REPORT.md 有说明，但应该在各 package 的 README.md 中

**建议改进：**
在每个 package 的 README.md 中添加"安全机制"章节

**示例（joystick_bridge/README.md）：**
```markdown
## 安全机制

### 手柄超时保护

**触发条件：**
- 当超过 `timeout_sec` 参数设定的时间（默认 0.5 秒）未收到 `/joystick_data` 话题时触发

**超时行为：**
1. 立即发布停止指令：`[0.0, 0.0, 0.0]` 到 `/local_driving`
2. 打印警告日志：`Joystick timeout - sending stop command`
3. 持续发送停止指令，直到重新收到 joystick_data

**参数配置：**
```bash
# 修改超时时间为 1 秒
ros2 run joystick_bridge joystick_bridge --ros-args \
  -p timeout_sec:=1.0
```

**默认参数：**
- `timeout_sec`: 0.5（秒）

**适用场景：**
- 手柄节点崩溃
- 手柄断开连接但节点未检测到
- 网络延迟导致消息丢失
```

---

### 3. **README.md 版本演进记录（建议）**

**AGENTS.md 要求：**
> README.md 被视为工程设计文档，而不是一次性说明
> 每次修改 README.md 时：
> - 不得删除上一版本内容
> - 推荐使用清晰的小标题区分不同阶段的设计说明

**建议改进：**
在各 package 的 README.md 中添加"更新记录"章节

```markdown
## 更新记录

### v2.0 - 2026-02-02
- ✅ 修复 Motor 3 无限重启问题（data[3] 解析）
- ✅ 添加手柄超时保护（500ms watchdog）
- ✅ 完善安全机制文档
- ✅ 优化启动脚本（支持 SSH 后台运行）

### v1.0 - 2026-01-30
- ✅ 实现基础手柄控制功能
- ✅ 实现全向轮运动学解算
- ✅ 实现达妙电机 CAN 驱动
- ✅ 手柄断开自动归零保护
```

---

## 🎯 改进优先级

### **P0 - 必须立即改进（安全相关）**
1. ✅ 手柄断开保护 - **已实现**
2. ⚠️ 话题超时检测 - **建议添加**

### **P1 - 应该改进（符合规范）**
1. ⚠️ README.md 补充超时说明
2. ⚠️ README.md 添加版本演进记录

### **P2 - 可选改进（提升质量）**
1. 添加更多测试用例
2. 添加性能监控
3. 添加更详细的调试日志

---

## 📊 总结

### **当前安全性评估：✅ 良好**
- 手柄断开保护完善
- 响应速度快（< 150ms）
- 多层安全机制

### **符合 AGENTS.md 规范：⚠️ 基本符合，建议改进**
- ✅ 使用 Python
- ✅ 完整注释
- ✅ 参数化配置
- ✅ 节点解耦
- ⚠️ 缺少话题超时检测（建议添加）
- ⚠️ README.md 超时说明不完整

### **建议行动：**
1. **立即可用：** 当前系统已经足够安全，可以正常使用
2. **后续改进：** 添加话题超时检测，完善文档
3. **速度调整：** 使用上述方法提高底盘速度

---

**评估日期：** 2026-02-02  
**评估结论：** 系统安全可用，建议添加超时检测进一步提升可靠性

---

## 2026-05-22 当前状态更新

本计划早期列出的 `joystick_bridge.py` 缺少 `/joystick_data` timeout 问题已经完成。当前版本包含三层控制链路保护：

- `joystick_bridge`: `/joystick_data` 超过 `input_timeout_sec = 0.3 s` 后发布 `/local_driving = [0,0,0]`
- `local_navigation_node`: `/local_driving` 超过 `command_timeout_sec = 0.3 s` 后 Motor 1-4 归零
- `damiao_node`: 连续 VEL 命令超过 `command_timeout_sec = 0.5 s` 后对应电机归零

当前上传 GitHub 前的最终实机确认记录见：

- `README.md` 顶部当前最终版说明
- `r1 final operation guide 1.0.md` 第 10 节
- `src/base_omniwheel_r2_700/README.md` v8 实机最终确认版

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
