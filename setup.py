#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version from __init__.py
def get_version():
    with open(os.path.join(this_directory, 'jetson_jolt', '__init__.py'), 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '0.1.0'

setup(
    name='jetson-jolt',
    version=get_version(),
    description='Command-line interface for NVIDIA Jetson setup and configuration',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jetson Setup Team',
    author_email='support@jetson-setup.com',
    url='https://github.com/OriNachum/jetson-jolt',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'jetson_jolt': ['scripts/*', 'config/*'],
    },
    install_requires=[
        'click>=8.0.0',
        'pyyaml>=6.0',
        'tabulate>=0.9.0',
        'packaging>=20.0',
        'psutil>=5.8.0',
        'rich>=12.0.0',
    ],
    entry_points={
        'console_scripts': [
            'jetson-jolt=jetson_jolt.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    python_requires='>=3.8',
    keywords='jetson nvidia embedded ai ml docker containers setup',
    project_urls={
        'Documentation': 'https://github.com/OriNachum/jetson-jolt/blob/main/README.md',
        'Bug Reports': 'https://github.com/OriNachum/jetson-jolt/issues',
        'Source': 'https://github.com/OriNachum/jetson-jolt',
    }
)