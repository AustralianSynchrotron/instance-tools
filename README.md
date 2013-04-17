instance-tools
==============

The instance tools comprise a collection of tools that are meant to run inside a cloud instance. They help to shutdown an instance, present the user with a welcome screen and more.

The current tools are:
* InstanceMonitor  
A python-based web service that provides functions to change the metadata of the instance or terminate the instance after a specified time.
* WelcomeScreen  
A configurable python-based GUI that allows users to start programs, websites or folders.


Python requirements:

- Python 2.6+

Required Python packages:

- Tornado 2.4.1+ (http://www.tornadoweb.org/)

Installation
------------

On Centos 6.3 (as root):

1. Ensure pip is installed: easy_install pip
2. Ensure git, gcc and python dev are installed: yum install -y git gcc python-devel
3. Install the instance tools from GitHub: pip install git+https://github.com/AustralianSynchrotron/instance-tools

On Ubuntu 12.10 (as user):

1. sudo apt-get update
2. sudo apt-get -y install python-pip
3. sudo apt-get -y install git
4. sudo pip install git+https://github.com/AustralianSynchrotron/instance-tools
