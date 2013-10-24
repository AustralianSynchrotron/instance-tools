#!/usr/bin/env python
#
# Copyright (c) 2013, Synchrotron Light Source Australia Pty Ltd
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the Australian Synchrotron nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 
import sys
import os
from PySide.QtCore import *
from PySide.QtGui import *
import xml.etree.ElementTree as ET



#-----------------------
#     Main classes
#-----------------------

class ArchiveCopy(QWidget):
    """The archive copy window."""

    def __init__(self, config_filename):
        QWidget.__init__(self)

        # Import XML document
        tree = ET.parse(config_filename)
        root = tree.getroot()

        # Get application settings
        self._node_settings = root.find('settings')



#-----------------------
#  Execute application
#-----------------------
def main():
    # read the configuration
    parser = argparse.ArgumentParser(prog='archivecopy',
                                     description='Archive copy')
    parser.add_argument('<config_file>', action='store',
                        help='Path to configuration file')
    args = vars(parser.parse_args())
    confPath = args['<config_file>']

    # start the application
    app = QApplication(sys.argv)
    widget = ArchiveCopy(confPath)
    widget.show()
    sys.exit(app.exec_())
