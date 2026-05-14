import os
from glob import glob
from setuptools import setup

package_name = 'joystick_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('lib', package_name), glob('scripts/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='EdUHK Robocon Team',
    maintainer_email='robotics@example.com',
    description='Bridge node to convert joystick input to omniwheel base navigation commands',
    license='Apache License 2.0',
    entry_points={},
)
