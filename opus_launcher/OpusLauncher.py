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
import shutil
import subprocess
from subprocess import Popen
from sys import platform
import argparse
from PySide.QtCore import *
from PySide.QtGui import *
import xml.etree.ElementTree as ET

#-----------------------
# OS dependent settings 
#-----------------------
if platform == "win32":
    # Disable the windows file system redirection for 32bit programs
    import ctypes
    ctypes.windll.kernel32.Wow64DisableWow64FsRedirection(ctypes.byref(ctypes.c_long()))


class OpusLauncher(QWidget):
    """The main opus launcher window."""

    def __init__(self, config_filename):
        QWidget.__init__(self)

        # Import XML document
        tree = ET.parse(config_filename)
        root = tree.getroot()

        # Get application settings
        self._node_settings = root.find('app')
        self._icon_path = os.path.join(os.path.dirname(os.path.abspath(config_filename)),
                                       self._node_settings.find('iconpath').text)

        # Get OPUS settings
        self._opus_settings = root.find('opus')

        # Create the layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Set title and title logo
        self.setWindowTitle(self._node_settings.find('title').text)
        logo = QPixmap(os.path.join(self._icon_path, self._node_settings.find('logo').text))
        logo_label = QLabel(self)
        #logo_label.setAutoFillBackground(True)
        #logo_palette = logo_label.palette()
        #logo_palette.setColor(QPalette.Window, Qt.white)
        #logo_label.setPalette(logo_palette)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setPixmap(logo)
        main_layout.addWidget(logo_label)

        # Add the instruction label
        instruction_text = self._node_settings.find('instruction').text
        instruction_label = QLabel(instruction_text, self)
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        # Get a list of the EPN folders
        self._src_path = root.find('source').text
        self._dest_path = root.find('destination').text
        epn_dirs = [name for name in os.listdir(self._src_path)
                    if os.path.isdir(os.path.join(self._src_path, name))]

        # Add the list widget and fill it with data
        self.epn_list = QListWidget(self)
        self.epn_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for epn_dir in epn_dirs:
            self.epn_list.addItem(epn_dir)
        main_layout.addWidget(self.epn_list)

        # Add the start launch button
        launch_button = QPushButton("Start OPUS")
        launch_button.setFixedHeight(50)
        launch_button.clicked.connect(self.launch_opus)
        main_layout.addWidget(launch_button)

        # Centre application window
        self.setMinimumSize(int(self._node_settings.find('width').text),
                            int(self._node_settings.find('height').text))
        desktop_widget = QApplication.desktop()
        screen_rect = desktop_widget.availableGeometry(self)
        self.move(screen_rect.center() - self.rect().center())

    def make_dirs(self, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)

    def source_dir(self, epn):
        return os.path.join(self._src_path, epn, "data")

    def count_files(self, epns):
        result = 0
        for epn in epns:
            files = []
            for path, dirs, filenames in os.walk(self.source_dir(epn)):
                files.extend(filenames)
            result += len(files)
        return result

    def launch_opus(self):
        # Check if the destination folder exists, if not create it
        self.make_dirs(self._dest_path)

        # Get selected EPNs
        epns = [epn.text() for epn in self.epn_list.selectedItems()]

        # Count the number of files that will be copied
        num_files = self.count_files(epns)

        # Copy the files and folders and report the progress
        if num_files > 0:
            # Show progress dialog
            progress = QProgressDialog("Copying experiments...", "Cancel",
                                       0, num_files, self)
            progress.setWindowModality(Qt.WindowModal)

            num_copied = 0
            for epn in epns:
                src  = self.source_dir(epn)
                dest = os.path.join(self._dest_path, epn)

                # Copy the EPN folder only if the EPN hasn't been copied yet
                if not os.path.exists(dest):
                    self.make_dirs(dest)

                    for path, dirs, filenames in os.walk(src):
                        for directory in dirs:
                            dest_dir = path.replace(src, dest)
                            self.make_dirs(os.path.join(dest_dir, directory))
                        for sfile in filenames:
                            src_file = os.path.join(path, sfile)
                            dest_file = os.path.join(path.replace(src, dest), sfile)
                            shutil.copy(src_file, dest_file)
                            num_copied += 1
                            progress.setValue(num_copied)
            progress.setValue(num_files)

        # Launch OPUS
        cmd = [self._opus_settings.find('cmd').text]
        cmd.append("/LANGUAGE=ENGLISH")
        Popen(cmd, cwd=self._opus_settings.find('cwd').text)

#-----------------------
#  Execute application
#-----------------------
def main():
    # read the configuration
    parser = argparse.ArgumentParser(prog='welcomescreen',
                                     description='Welcome Screen GUI')
    parser.add_argument('<config_file>', action='store',
                        help='Path to configuration file')
    args = vars(parser.parse_args())
    confPath = args['<config_file>']

    # start the application
    app = QApplication(sys.argv)
    widget = OpusLauncher(confPath)
    widget.show()
    sys.exit(app.exec_())
