from setuptools import find_packages, setup

package_name = 'task01'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/task1.launch']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='denk',
    maintainer_email='denk@example.com',
    description='Task 1 package with receiver node.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'receiver = task01.receiver:main',
        ],
    },
)
