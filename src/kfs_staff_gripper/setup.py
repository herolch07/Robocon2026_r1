from setuptools import find_packages, setup

package_name = "kfs_staff_gripper"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "README.md", "TODO.md"]),
    ],
    install_requires=["setuptools", "pyserial"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="EdUHK Robocon Team",
    maintainer_email="robotics@example.com",
    description="Arduino Mega three-relay driver and joystick bridge for the KFS staff gripper",
    license="Apache License 2.0",
    entry_points={
        "console_scripts": [
            "kfs_staff_gripper_arduino_node = kfs_staff_gripper.kfs_staff_gripper_arduino_node:main",
            "kfs_staff_gripper_joystick_bridge_node = kfs_staff_gripper.kfs_staff_gripper_joystick_bridge_node:main",
        ],
    },
)
