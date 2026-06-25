#!/bin/bash
# 简单的启动脚本 - 在4个独立终端中启动所有节点
# 使用 gnome-terminal 打开多个终端窗口

set -e

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  启动底盘控制系统 - R2-700"
echo "=========================================="
echo ""

# 检查 gnome-terminal 是否可用
if ! command -v gnome-terminal &> /dev/null; then
    echo "❌ 错误：未找到 gnome-terminal"
    echo "   请手动在4个终端中运行以下命令："
    echo ""
    echo "终端1: source $WS_DIR/install/setup.bash && ros2 run base_omniwheel_r2_700 damiao_node"
    echo "终端2: source $WS_DIR/install/setup.bash && ros2 run base_omniwheel_r2_700 local_navigation_node"
    echo "终端3: source $WS_DIR/install/setup.bash && ros2 run my_joystick_driver joystick_node"
    echo "终端4: source $WS_DIR/install/setup.bash && ros2 run joystick_bridge joystick_bridge"
    exit 1
fi

echo "✅ 启动节点..."
echo ""

# 启动电机驱动节点
gnome-terminal --title="1. 电机驱动 (damiao_node)" -- bash -c "
cd $WS_DIR
source install/setup.bash
echo '=========================================='
echo '  电机驱动节点 (Motor Controller)'
echo '=========================================='
echo ''
ros2 run base_omniwheel_r2_700 damiao_node
exec bash
"

sleep 1

# 启动运动学节点
gnome-terminal --title="2. 运动学 (local_navigation_node)" -- bash -c "
cd $WS_DIR
source install/setup.bash
echo '=========================================='
echo '  运动学节点 (Local Navigation)'
echo '=========================================='
echo ''
ros2 run base_omniwheel_r2_700 local_navigation_node
exec bash
"

sleep 0.5

# 启动手柄驱动
gnome-terminal --title="3. 手柄驱动 (joystick_node)" -- bash -c "
cd $WS_DIR
source install/setup.bash
echo '=========================================='
echo '  手柄驱动 (Joystick Driver)'
echo '=========================================='
echo ''
ros2 run my_joystick_driver joystick_node
exec bash
"

sleep 0.5

# 启动手柄桥接
gnome-terminal --title="4. 手柄桥接 (joystick_bridge)" -- bash -c "
cd $WS_DIR
source install/setup.bash
echo '=========================================='
echo '  手柄桥接 (Joystick Bridge)'
echo '=========================================='
echo ''
ros2 run joystick_bridge joystick_bridge
exec bash
"

echo "=========================================="
echo "✅ 所有节点已启动！"
echo "=========================================="
echo ""
echo "📌 已打开4个终端窗口："
echo "   1. 电机驱动 (damiao_node)"
echo "   2. 运动学节点 (local_navigation_node)"
echo "   3. 手柄驱动 (joystick_node)"
echo "   4. 手柄桥接 (joystick_bridge)"
echo ""
echo "🎮 手柄控制："
echo "   左摇杆：控制底盘平移"
echo "   右摇杆：控制底盘旋转"
echo ""
echo "🛑 关闭系统："
echo "   在每个终端窗口按 Ctrl+C"
echo ""
