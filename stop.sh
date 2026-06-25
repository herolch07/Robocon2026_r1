#!/bin/bash
# 停止所有后台运行的节点 - 增强版

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$WS_DIR/.pids"

echo "=========================================="
echo "  停止底盘控制系统"
echo "=========================================="
echo ""

echo "正在停止所有节点..."
echo ""

# 方法1：从 PID 文件读取并停止
if [ -f "$PID_FILE" ]; then
    echo "停止脚本启动的节点..."
    while read -r pid; do
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# 方法2：停止所有可能的 Python 实现的节点
echo "停止所有 ROS2 Python 节点..."

# 停止 platformio Python 的节点
pkill -9 -f "platformio/penv/bin/python.*joystick"
pkill -9 -f "platformio/penv/bin/python.*navigation"
pkill -9 -f "platformio/penv/bin/python.*damiao"
pkill -9 -f "platformio/penv/bin/python.*base_omniwheel"

# 停止系统 Python3 的节点
pkill -9 -f "python3.*joystick"
pkill -9 -f "python3.*navigation"
pkill -9 -f "python3.*damiao"
pkill -9 -f "python3.*motor_controller"

# 停止通过 ros2 run 启动的节点
pkill -9 -f "ros2 run base_omniwheel_r2_700"
pkill -9 -f "ros2 run my_joystick_driver"
pkill -9 -f "ros2 run joystick_bridge"

sleep 1

echo ""
echo "=========================================="
echo "✅ 停止命令已执行"
echo "=========================================="
echo ""

# 验证是否全部停止
echo "验证节点状态..."
sleep 1

# 重启 ROS2 守护进程以清理缓存
echo "重启 ROS2 守护进程..."
ros2 daemon stop 2>/dev/null
sleep 1
ros2 daemon start 2>/dev/null
sleep 1

# 检查是否还有节点
NODES=$(ros2 node list 2>/dev/null)

if [ -z "$NODES" ]; then
    echo "✅ 所有节点已完全停止"
else
    echo "⚠️  检测到以下节点可能还在运行："
    echo "$NODES"
    echo ""
    echo "如果这些是旧的缓存，将在几秒后自动清除"
    echo "如果确实还在运行，请运行："
    echo "  pkill -9 -f python"
    echo "  ros2 daemon stop && ros2 daemon start"
fi

echo ""
echo "提示：如果手柄还能控制机器人，说明还有节点在运行"
echo "      请运行：ps aux | grep -E 'joystick|motor|damiao' | grep -v grep"
echo ""
