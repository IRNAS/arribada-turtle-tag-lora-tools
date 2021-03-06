from __future__ import unicode_literals

import re

from setuptools import setup, find_packages


def get_version(filename):
    content = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
    return metadata['version']


setup(
    name='arribada_tools',
    version=get_version('arribada_tools/__init__.py'),
    url='https://tbd',
    license='GNU General Public License v3 or later (GPLv3+)',
    author='Liam Wickins',
    author_email='liam@icoteq.com',
    description='Python tools for provisioning Arribada tracker devices',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'PyYAML == 3.12',
        'pyusb >= 1.0.2',
        'pyserial >= 3.4',
        'bluepy >= 1.1.4;platform_system=="Linux"',
        'python-dateutil >= 2.6.1',
        'libusb1 >= 1.6.4',
        'awscli >= 1.16.105',
        'aws-sam-cli >= 0.15.0',
        'botocore >= 1.12.116',
        'boto3 >= 1.9.116',
        'cryptography >= 2.4.2',
        'pyOpenSSL >= 19.0.0',
        'httplib2 >= 0.12.0',
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'mock >= 1.0',
    ],
    scripts=[
        'tests/tracker_config',
        'tests/gps_almanac',
        'tests/gps_ascii_config',
        'tests/log_parse',
        'tests/ble_scan',
        'tests/ble_auto',
        'tests/aws_config',
        'tests/cellular_config',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: Communications',
    ],
)
