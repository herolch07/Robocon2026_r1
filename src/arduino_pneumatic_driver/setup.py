from setuptools import find_packages, setup

package_name = "arduino_pneumatic_driver"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pyserial"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="EdUHK Robocon Team",
    maintainer_email="robotics@example.com",
    description="Arduino Mega USB serial driver for pneumatic relay gripper",
    license="Apache License 2.0",
    entry_points={
        "console_scripts": [
            "pneumatic_relay_driver_node = arduino_pneumatic_driver.pneumatic_relay_driver_node:main",
            "pneumatic_gripper_joystick_bridge_node = arduino_pneumatic_driver.pneumatic_gripper_joystick_bridge_node:main",
        ],
    },
)
