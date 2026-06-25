from setuptools import find_packages, setup


package_name = "robot_power_control"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="EdUHK Robocon Team",
    maintainer_email="robotics@example.com",
    description="Joystick-triggered robot power management nodes.",
    license="Apache License 2.0",
    entry_points={
        "console_scripts": [
            "joystick_shutdown_node = robot_power_control.joystick_shutdown_node:main",
        ],
    },
)
