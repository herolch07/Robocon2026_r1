from setuptools import find_packages, setup

package_name = 'r1_arm_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='EdUHK Robocon Team',
    maintainer_email='robotics@example.com',
    description='R1 arm control package',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'elevator_controller_node = r1_arm_control.elevator_controller_node:main',
            'elevator_joystick_bridge_node = r1_arm_control.elevator_joystick_bridge_node:main',
            'horizontal_controller_node = r1_arm_control.horizontal_controller_node:main',
            'horizontal_joystick_bridge_node = r1_arm_control.horizontal_joystick_bridge_node:main',
            'arm_gripper_controller_node = r1_arm_control.arm_gripper_controller_node:main',
            'arm_gripper_joystick_bridge_node = r1_arm_control.arm_gripper_joystick_bridge_node:main',
            'motor7_position_controller_node = r1_arm_control.motor7_position_controller_node:main',
            'motor8_position_controller_node = r1_arm_control.motor8_position_controller_node:main',
            'motor_position_selector_joystick_bridge_node = r1_arm_control.motor_position_selector_joystick_bridge_node:main',
        ],
    },
)
