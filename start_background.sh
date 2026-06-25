#!/bin/bash
# SSH 简单启动脚本 - 所有节点在后台运行，日志输出到文件

set -e

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$WS_DIR/logs"

echo "=========================================="
echo "  启动底盘控制系统 - R2-700"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p "$LOG_DIR"

# 清理旧的日志文件
rm -f "$LOG_DIR"/*.log

echo "✅ 准备启动所有节点..."
echo ""

# 加载 ROS2 环境
cd "$WS_DIR"
source install/setup.bash

# 启动电机驱动节点（后台运行）
echo "[1/4] 启动电机驱动节点 (damiao_node)..."
nohup ros2 run base_omniwheel_r2_700 damiao_node > "$LOG_DIR/damiao_node.log" 2>&1 &
DAMIAO_PID=$!
sleep 1

# 检查是否启动成功
if ps -p $DAMIAO_PID > /dev/null; then
    echo "      ✅ 电机驱动节点已启动 (PID: $DAMIAO_PID)"
else
    echo "      ❌ 电机驱动节点启动失败"
    exit 1
fi

# 启动运动学节点（后台运行）
echo "[2/4] 启动运动学节点 (local_navigation_node)..."
nohup ros2 run base_omniwheel_r2_700 local_navigation_node > "$LOG_DIR/local_navigation_node.log" 2>&1 &
NAV_PID=$!
sleep 0.5

# 检查是否启动成功
if ps -p $NAV_PID > /dev/null; then
    echo "      ✅ 运动学节点已启动 (PID: $NAV_PID)"
else
    echo "      ❌ 运动学节点启动失败"
    kill $DAMIAO_PID 2>/dev/null
    exit 1
fi

# 启动手柄驱动（后台运行）
echo "[3/4] 启动手柄驱动 (joystick_node)..."
nohup ros2 run my_joystick_driver joystick_node > "$LOG_DIR/joystick_node.log" 2>&1 &
JOY_PID=$!
sleep 0.5

# 检查是否启动成功
if ps -p $JOY_PID > /dev/null; then
    echo "      ✅ 手柄驱动已启动 (PID: $JOY_PID)"
else
    echo "      ❌ 手柄驱动启动失败"
    kill $DAMIAO_PID $NAV_PID 2>/dev/null
    exit 1
fi

# 启动手柄桥接（后台运行）
echo "[4/4] 启动手柄桥接 (joystick_bridge)..."
nohup "$WS_DIR/install/joystick_bridge/bin/joystick_bridge" > "$LOG_DIR/joystick_bridge.log" 2>&1 &
BRIDGE_PID=$!
sleep 0.5

# 检查是否启动成功
if ps -p $BRIDGE_PID > /dev/null; then
    echo "      ✅ 手柄桥接已启动 (PID: $BRIDGE_PID)"
else
    echo "      ❌ 手柄桥接启动失败"
    kill $DAMIAO_PID $NAV_PID $JOY_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有节点启动成功！"
echo "=========================================="
echo ""
echo "📊 进程信息："
echo "   电机驱动:   PID $DAMIAO_PID"
echo "   运动学节点: PID $NAV_PID"
echo "   手柄驱动:   PID $JOY_PID"
echo "   手柄桥接:   PID $BRIDGE_PID"
echo ""
echo "📁 日志文件位置："
echo "   $LOG_DIR/damiao_node.log"
echo "   $LOG_DIR/local_navigation_node.log"
echo "   $LOG_DIR/joystick_node.log"
echo "   $LOG_DIR/joystick_bridge.log"
echo ""
echo "📖 常用命令："
echo "   查看所有节点: ros2 node list"
echo "   查看话题:     ros2 topic list"
echo "   实时查看日志: tail -f $LOG_DIR/damiao_node.log"
echo "   停止所有节点: $WS_DIR/stop.sh"
echo ""
echo "🎮 手柄控制："
echo "   左摇杆: 控制底盘平移"
echo "   右摇杆: 控制底盘旋转"
echo ""

# 保存 PID 到文件，方便停止
echo "$DAMIAO_PID" > "$WS_DIR/.pids"
echo "$NAV_PID" >> "$WS_DIR/.pids"
echo "$JOY_PID" >> "$WS_DIR/.pids"
echo "$BRIDGE_PID" >> "$WS_DIR/.pids"

echo "提示: 节点在后台运行，可以安全关闭此终端"
echo ""
