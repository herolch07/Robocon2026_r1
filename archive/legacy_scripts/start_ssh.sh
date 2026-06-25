#!/bin/bash
# SSH 远程启动脚本 - 使用 tmux 在后台管理节点
# 适用于 SSH 连接时使用（无图形界面）

set -e

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  启动底盘控制系统 - R2-700 (SSH 版本)"
echo "=========================================="
echo ""

# 检查 tmux 是否安装
if ! command -v tmux &> /dev/null; then
    echo "❌ 错误：未安装 tmux"
    echo "   请运行：sudo apt install tmux"
    exit 1
fi

# 会话名称
SESSION="robocon_control"

# 检查会话是否已存在
if tmux has-session -t $SESSION 2>/dev/null; then
    echo "⚠️  会话 '$SESSION' 已存在"
    echo "   是否要关闭旧会话并重新启动？(y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "正在关闭旧会话..."
        tmux kill-session -t $SESSION
    else
        echo "取消启动。"
        echo "提示：使用 'tmux attach -t $SESSION' 连接到现有会话"
        exit 0
    fi
fi

# 工作目录

echo "✅ 创建 tmux 会话：$SESSION"
echo ""

# 创建 tmux 会话并启动第一个节点（电机驱动）
tmux new-session -d -s $SESSION -n "motors" "cd $WS_DIR && source install/setup.bash && echo '🔌 启动电机驱动节点...' && ros2 run base_omniwheel_r2_700 damiao_node; read"

# 等待一下确保第一个节点启动
sleep 1

# 创建第二个窗口（运动学节点）
tmux new-window -t $SESSION:1 -n "navigation" "cd $WS_DIR && source install/setup.bash && echo '⚙️  启动运动学节点...' && ros2 run base_omniwheel_r2_700 local_navigation_node; read"

# 等待一下
sleep 0.5

# 创建第三个窗口（手柄驱动）
tmux new-window -t $SESSION:2 -n "joystick" "cd $WS_DIR && source install/setup.bash && echo '🎮 启动手柄驱动...' && ros2 run my_joystick_driver joystick_node; read"

# 等待一下
sleep 0.5

# 创建第四个窗口（手柄桥接）
tmux new-window -t $SESSION:3 -n "bridge" "cd $WS_DIR && source install/setup.bash && echo '🌉 启动手柄桥接节点...' && ros2 run joystick_bridge joystick_bridge; read"

# 创建监控窗口
tmux new-window -t $SESSION:4 -n "monitor" "cd $WS_DIR && source install/setup.bash && echo '📊 监控窗口' && echo '' && echo '可用命令：' && echo '  ros2 topic list' && echo '  ros2 topic echo /joystick_data' && echo '  ros2 topic echo /local_driving' && echo '  ros2 topic echo /damiao_control' && echo '  ros2 topic hz /joystick_data' && echo '' && bash"

# 选择第一个窗口
tmux select-window -t $SESSION:0

echo "=========================================="
echo "✅ 所有节点已启动！"
echo "=========================================="
echo ""
echo "📌 tmux 会话信息："
echo "   会话名称: $SESSION"
echo ""
echo "🪟 窗口列表："
echo "   0: motors     - 电机驱动节点"
echo "   1: navigation - 运动学节点"
echo "   2: joystick   - 手柄驱动"
echo "   3: bridge     - 手柄桥接"
echo "   4: monitor    - 监控窗口"
echo ""
echo "📖 tmux 操作指南："
echo "   连接到会话：  tmux attach -t $SESSION"
echo "   切换窗口：    Ctrl+b 然后按 0-4"
echo "   分离会话：    Ctrl+b 然后按 d"
echo "   关闭会话：    tmux kill-session -t $SESSION"
echo ""
echo "🎮 手柄控制："
echo "   左摇杆：控制底盘平移方向"
echo "   右摇杆：控制底盘旋转"
echo ""
echo "现在连接到 tmux 会话..."
sleep 2

# 连接到 tmux 会话
tmux attach -t $SESSION
