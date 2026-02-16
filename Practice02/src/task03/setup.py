from setuptools import find_packages, setup

package_name = 'task03'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/task03.launch']),
        ('share/' + package_name + '/config', ['config/task03.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='denk',
    maintainer_email='denksworkspace@gmail.com',
    description='Task 3 package with Trigger proxy service.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'trigger_proxy = task03.trigger_proxy:main',
        ],
    },
)
