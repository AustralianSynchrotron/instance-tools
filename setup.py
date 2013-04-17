from __future__ import with_statement
from distutils.core import setup


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='InstanceTools',
    version='0.1',
    description='A collection of tools that are meant to run inside a cloud instance',
    long_description=long_description,
    url='https://github.com/AustralianSynchrotron/instance-tools',
    author='Andreas Moll',
    author_email='andreas.moll@synchrotron.org.au',
    packages=['instance_monitor', 'welcome_screen'],
    install_requires=[
        'argparse',
        'tornado >= 2.4.1',
    ],
    classifiers=[
        'Environment :: OpenStack',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Modified BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
    ],
    license='Modified BSD',
    scripts=['instmonitord'],
)
