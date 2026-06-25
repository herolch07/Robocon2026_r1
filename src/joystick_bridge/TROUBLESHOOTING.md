> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# Joystick Bridge 故障排查文档

## 问题记录：ros2 run 报错 "No executable found"

> 当前状态说明：当前 `src/joystick_bridge/setup.py` 使用 `scripts/joystick_bridge` 安装到 `lib/joystick_bridge/`，`entry_points` 为空。这与本历史排查文档中“同时保留 entry_points”的修复写法不同，但当前工作区的脚本安装方式是有效的。

**问题发生时间**：2026-02-03  
**影响版本**：v1.0.0  
**修复版本**：v1.0.1  
**符合规范**：AGENTS.md 9.2（README 演进规则）

---

## 问题描述

### 现象
用户尝试运行 `joystick_bridge` 节点时遇到以下错误：

```bash
$ ros2 run joystick_bridge joystick_bridge
No executable found
```

### 环境信息
- **ROS2 发行版**：Jazzy
- **操作系统**：Ubuntu 24.04 / Linux 6.8.0-1044-raspi
- **Python 版本**：3.12
- **工作空间**：`/home/robotics/robocon2026_r1/r1_control_ws`

---

## 问题分析

### 根本原因

ROS2 Python package 的可执行文件安装需要满足两个条件：

1. **在 `setup.py` 中定义 `entry_points`**（历史方案；当前工作区改为 `entry_points={}` 并安装 `scripts/joystick_bridge`）
   ```python
   entry_points={
       'console_scripts': [
           'joystick_bridge = joystick_bridge.joystick_bridge:main',
       ],
   }
   ```

2. **在安装目录中存在实际的可执行脚本文件**（缺失）
   - 需要在 `install/<package>/lib/<package>/` 目录下存在同名可执行文件
   - 仅有 `entry_points` 定义不足以让 `ros2 run` 找到可执行文件

### 技术细节

#### ROS2 查找可执行文件的机制

`ros2 run` 命令的查找路径为：
```
$AMENT_PREFIX_PATH/<package>/lib/<package>/<executable>
```

对比正常工作的 `my_joystick_driver` package：
```bash
# ✅ 正常工作
$ ls install/my_joystick_driver/lib/my_joystick_driver/
joystick_node

$ ros2 pkg executables my_joystick_driver
my_joystick_driver joystick_node  # 能够找到
```

而 `joystick_bridge` 初始版本：
```bash
# ❌ 缺少可执行文件
$ ls install/joystick_bridge/lib/
python3.12/  # 只有 Python 包，没有 joystick_bridge 目录

$ ros2 pkg executables joystick_bridge
# 空输出，找不到可执行文件
```

#### 为什么仅定义 entry_points 不够？

虽然 Python setuptools 的 `entry_points` 可以生成可执行脚本（通常在 `bin/` 目录），但 ROS2 的 `ros2 run` 命令：

1. **不使用 Python 的 `bin/` 目录**
2. **需要在 `lib/<package>/` 目录下查找可执行文件**
3. **依赖 ament 工具链的安装约定**

---

## 解决方案

### 修复步骤

#### 1. 创建可执行脚本文件

创建 `scripts/joystick_bridge` 文件：

```bash
mkdir -p src/joystick_bridge/scripts
```

文件内容：
```python
#!/usr/bin/env python3
"""
Joystick Bridge Node - ROS2 executable wrapper
"""
from joystick_bridge.joystick_bridge import main

if __name__ == '__main__':
    main()
```

赋予执行权限：
```bash
chmod +x src/joystick_bridge/scripts/joystick_bridge
```

#### 2. 修改 setup.py

在 `data_files` 中添加 scripts 安装路径：

```python
from setuptools import setup
import os
from glob import glob

package_name = 'joystick_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # ✅ 新增：安装可执行脚本到 lib/joystick_bridge/
        (os.path.join('lib', package_name), glob('scripts/*'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='EdUHK Robocon Team',
    maintainer_email='robotics@example.com',
    description='Bridge node to convert joystick input to omniwheel base navigation commands',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'joystick_bridge = joystick_bridge.joystick_bridge:main',
        ],
    },
)
```

**关键修改**：
- 导入 `os` 和 `glob` 模块
- 添加 `(os.path.join('lib', package_name), glob('scripts/*'))` 到 `data_files`
- 这会将 `scripts/` 目录中的所有文件复制到安装目录的 `lib/joystick_bridge/`

#### 3. 重新编译

```bash
cd /home/robotics/robocon2026_r1/r1_control_ws
rm -rf build/joystick_bridge install/joystick_bridge
colcon build --packages-select joystick_bridge
source install/setup.bash
```

#### 4. 验证修复

```bash
# 检查可执行文件是否安装
$ ls install/joystick_bridge/lib/joystick_bridge/
joystick_bridge  # ✅ 文件存在

# 检查 ros2 是否能找到
$ ros2 pkg executables joystick_bridge
joystick_bridge joystick_bridge  # ✅ 能够找到

# 测试运行
$ ros2 run joystick_bridge joystick_bridge
[INFO] [joystick_bridge]: Joystick bridge node initialized
[INFO] [joystick_bridge]: Max speed: 150.0 cm/s
[INFO] [joystick_bridge]: Translation curve: y = a*x + (1-a)*x^3, a=0.1
[INFO] [joystick_bridge]: Rotation curve: y = a*x + (1-a)*x^3, a=0.1
[INFO] [joystick_bridge]: Max rotation: 3.0 rad/s
[INFO] [joystick_bridge]: Deadzone: 15
# ✅ 成功启动
```

---

## 额外修复：destroy_node() 异常处理

### 问题现象

在节点关闭时（Ctrl+C 或 timeout）会出现以下错误：

```
rclpy._rclpy_pybind11.RCLError: Failed to publish: publisher's context is invalid
```

### 原因分析

当 ROS2 上下文关闭时（如收到 `SIGTERM` 或 `ExternalShutdownException`），尝试发布消息会失败，因为 publisher 的上下文已经无效。

### 修复代码

修改 `joystick_bridge.py` 中的 `destroy_node()` 方法：

```python
def destroy_node(self):
    """节点销毁时的安全处理"""
    try:
        # 发送停止指令
        stop_msg = Float32MultiArray()
        stop_msg.data = [0.0, 0.0, 0.0]
        self.nav_pub.publish(stop_msg)
        self.get_logger().info("Joystick bridge stopped - sent stop command")
    except Exception as e:
        # 如果上下文已经关闭，忽略错误
        pass
    finally:
        super().destroy_node()
```

**改进点**：
- 使用 try-except-finally 结构
- 捕获上下文关闭时的发布错误
- 确保 `super().destroy_node()` 始终被调用

---

## 经验总结

### 工程实践要点

1. **ROS2 Python package 必须同时具备**：
   - `entry_points` 定义（供 Python 导入）
   - 实际的可执行脚本文件（供 `ros2 run` 查找）

2. **setup.py 的 data_files 配置**：
   ```python
   data_files=[
       # 标准 ROS2 资源文件
       ('share/ament_index/resource_index/packages', [...]),
       ('share/' + package_name, ['package.xml']),
       
       # 可执行脚本（关键）
       (os.path.join('lib', package_name), glob('scripts/*'))
   ]
   ```

3. **目录结构规范**：
   ```
   my_package/
   ├── my_package/           # Python 模块
   │   ├── __init__.py
   │   └── my_node.py
   ├── scripts/              # 可执行脚本（新增）
   │   └── my_node
   ├── resource/
   ├── package.xml
   └── setup.py
   ```

4. **节点关闭安全性**：
   - 所有涉及 ROS2 通信的清理操作都应使用 try-except 包裹
   - 避免在上下文已关闭后尝试发布消息

### 调试技巧

当遇到 "No executable found" 错误时，按以下顺序排查：

1. **检查安装目录结构**：
   ```bash
   ls install/<package>/lib/<package>/
   ```
   应该存在与 `entry_points` 中同名的可执行文件

2. **检查 ros2 是否识别**：
   ```bash
   ros2 pkg executables <package>
   ```
   应该输出可执行文件列表

3. **检查文件权限**：
   ```bash
   ls -la install/<package>/lib/<package>/<executable>
   ```
   应该具有执行权限（-rwxr-xr-x）

4. **检查 AMENT_PREFIX_PATH**：
   ```bash
   echo $AMENT_PREFIX_PATH
   ```
   应该包含当前工作空间的 install 目录

---

## 参考资料

### ROS2 官方文档
- [Creating a Python Package](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html)
- [setup.py Configuration](https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Python-Documentation.html)

### 相关 AGENTS.md 规范
- **9.2 README 演进规则**：不得删除旧版本内容，必须记录修改历史
- **9.3 语言优先级**：优先使用 Python 并提供充足注释
- **6. 输出要求**：必须给出可直接使用的代码和文档

---

## 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| v1.0.1 | 2026-02-03 | 修复 ros2 run 可执行文件缺失问题 |
| v1.0.0 | 2026-01-30 | 初始版本 |

---

**维护者**：EdUHK Robocon Robotics Team  
**最后更新**：2026-02-03

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
