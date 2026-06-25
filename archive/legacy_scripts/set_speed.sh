#!/bin/bash
# 速度调整脚本 - 动态调整底盘最大速度和旋转速度

echo "=========================================="
echo "  底盘速度调整工具"
echo "=========================================="
echo ""

# 检查 joystick_bridge 节点是否在运行
if ! ros2 node list 2>/dev/null | grep -q "joystick_bridge"; then
    echo "❌ 错误：joystick_bridge 节点未运行"
    echo "   请先启动系统：./start.sh 或 ./start_background.sh"
    exit 1
fi

echo "✅ 检测到 joystick_bridge 节点正在运行"
echo ""

# 显示当前设置
echo "📊 当前设置："
CURRENT_SPEED=$(ros2 param get /joystick_bridge max_speed_cm 2>/dev/null | grep -oP '\d+\.\d+|\d+')
CURRENT_ROTATION=$(ros2 param get /joystick_bridge max_rotation 2>/dev/null | grep -oP '\d+\.\d+|\d+')

echo "   最大速度:   ${CURRENT_SPEED} cm/s"
echo "   最大旋转:   ${CURRENT_ROTATION} rad/s"
echo ""

# 显示预设选项
echo "=========================================="
echo "选择速度等级："
echo "=========================================="
echo "1. 慢速   - 100 cm/s (1 m/s)   - 测试/调试用"
echo "2. 中速   - 150 cm/s (1.5 m/s) - 正常练习"
echo "3. 快速   - 200 cm/s (2 m/s)   - 比赛速度"
echo "4. 极速   - 300 cm/s (3 m/s)   - 最大性能（谨慎）"
echo "5. 自定义 - 手动输入速度"
echo "0. 退出"
echo ""

read -p "请选择 [0-5]: " choice

case $choice in
    1)
        NEW_SPEED=100.0
        NEW_ROTATION=2.0
        LEVEL="慢速"
        ;;
    2)
        NEW_SPEED=150.0
        NEW_ROTATION=2.5
        LEVEL="中速"
        ;;
    3)
        NEW_SPEED=200.0
        NEW_ROTATION=3.0
        LEVEL="快速"
        ;;
    4)
        NEW_SPEED=300.0
        NEW_ROTATION=4.0
        LEVEL="极速"
        ;;
    5)
        echo ""
        read -p "请输入最大速度 (cm/s): " NEW_SPEED
        read -p "请输入最大旋转速度 (rad/s): " NEW_ROTATION
        LEVEL="自定义"
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "正在设置速度为：$LEVEL"
echo "=========================================="
echo ""

# 设置新的参数
echo "设置 max_speed_cm = ${NEW_SPEED}..."
ros2 param set /joystick_bridge max_speed_cm $NEW_SPEED

echo "设置 max_rotation = ${NEW_ROTATION}..."
ros2 param set /joystick_bridge max_rotation $NEW_ROTATION

echo ""
echo "=========================================="
echo "✅ 速度设置成功！"
echo "=========================================="
echo ""
echo "新设置："
echo "   最大速度:   ${NEW_SPEED} cm/s ($(echo "scale=2; $NEW_SPEED/100" | bc) m/s)"
echo "   最大旋转:   ${NEW_ROTATION} rad/s"
echo ""
echo "⚠️  注意事项："
echo "   - 设置立即生效，无需重启节点"
echo "   - 推动手柄摇杆到顶时会达到最大速度"
echo "   - 如果速度太快请小心控制"
echo "   - 重新启动节点后会恢复默认值 (100 cm/s)"
echo ""
