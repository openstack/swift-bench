#!/usr/bin/python
# Copyright (c) 2010-2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

from swiftbench import __version__ as version


name = 'swift-bench'

with open('requirements.txt', 'r') as f:
    requires = [x.strip() for x in f if x.strip()]


setup(
    name=name,
    version=version,
    description='Benchmark tool for OpenStack Swift',
    license='Apache License (2.0)',
    author='OpenStack',
    author_email='openstack-dev@lists.openstack.org',
    url='http://openstack.org',
    packages=find_packages(exclude=['test', 'bin']),
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: OpenStack',
    ],
    install_requires=requires,
    scripts=[
        'bin/swift-bench',
        'bin/swift-bench-client',
    ],
)
