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
import threading
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

        # Get settings
        self._node_settings = root.find('app')
        self._title = self._node_settings.find('title').text
        self._opus_settings = root.find('opus')

        # Create the main layout
        self._main_layout = QVBoxLayout()
        self.setLayout(self._main_layout)

        # Create the different widgets and set the default
        self._epn_widget = self.create_widget_epn(root)
        self._progress_widget = self.create_widget_progress()
        self._launch_widget = self.create_widget_launch()
        self._main_layout.addWidget(self._epn_widget)
        self._main_layout.addWidget(self._progress_widget)
        self._main_layout.addWidget(self._launch_widget)
        self._progress_widget.setVisible(False)
        self._launch_widget.setVisible(False)

        # Create title
        self.setWindowTitle(self._title)

        # Centre application window
        self.setMinimumSize(int(self._node_settings.find('width').text),
                            int(self._node_settings.find('height').text))
        desktop_widget = QApplication.desktop()
        screen_rect = desktop_widget.availableGeometry(self)
        self.move(screen_rect.center() - self.rect().center())


    def add_title(self, layout):
        title_label = QLabel(self._title, self)
        font = title_label.font()
        font.setPointSize(48)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)


    def enable_launch_button(self):
        if len(self._epn_list.selectedItems()) > 0:
            self._launch_button.setEnabled(True)


    def create_widget_epn(self, root):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.add_title(layout)

        # Add the instruction label
        instruction_text = self._node_settings.find('instruction').text
        instruction_label = QLabel(instruction_text, self)
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)

        # Get a list of the EPN folders
        self._src_path = root.find('source').text
        self._dest_path = root.find('destination').text
        epn_dirs = [name for name in os.listdir(self._src_path)
                    if os.path.isdir(os.path.join(self._src_path, name))]

        # Add the list widget and fill it with data
        self._epn_list = QListWidget(self)
        self._epn_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._epn_list.itemSelectionChanged.connect(self.enable_launch_button)
        for epn_dir in epn_dirs:
            self._epn_list.addItem(epn_dir)
        layout.addWidget(self._epn_list)

        # Add the start launch button
        self._launch_button = QPushButton("Start OPUS")
        self._launch_button.setFixedHeight(50)
        self._launch_button.clicked.connect(self.launch_opus)
        self._launch_button.setEnabled(False)
        layout.addWidget(self._launch_button)
        return widget


    def create_widget_progress(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.add_title(layout)

        # Add the subtitle label
        subtitle_label = QLabel("Copying the files for the selected experiment(s) "+
                                "from the archive to the local drive.", self)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        # Add the filename label
        layout.addStretch(1)
        self._progress_label = QLabel(self)
        self._progress_label.setWordWrap(True)
        layout.addWidget(self._progress_label)

        # Add the progress bar
        self._progress_bar = QProgressBar(self)
        layout.addWidget(self._progress_bar)
        layout.addStretch(1)
        return widget


    def create_widget_launch(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.add_title(layout)
        layout.addStretch(1)
        self._launch_label = QLabel("Launching OPUS (might take a few minutes)...",
                                    self)
        self._launch_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._launch_label)
        layout.addStretch(1)

        # Add the close button
        close_button = QPushButton("Close")
        close_button.setFixedHeight(50)
        close_button.clicked.connect(exit)
        layout.addWidget(close_button)
        return widget


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
        # Show the progress widget
        self._epn_widget.hide()
        self._progress_widget.show()
        QApplication.processEvents()

        # Check if the destination folder exists, if not create it
        self.make_dirs(self._dest_path)
 
        # Get selected EPNs
        epns = [epn.text() for epn in self._epn_list.selectedItems()]

        # Count the number of files that will be copied
        num_files = self.count_files(epns)

        # Copy the files and folders and report the progress
        if num_files > 0:
            num_copied = 0
            self._progress_bar.setMaximum(num_files)
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
                            self._progress_label.setText(sfile)
                            self._progress_bar.setValue(num_copied)
            self._progress_bar.setValue(num_files)

        # Show the launch widget and launch OPUS
        self._progress_widget.hide()
        self._launch_widget.show()
        QApplication.processEvents()
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
    widget.setWindowFlags(Qt.WindowStaysOnTopHint)
    widget.show()
    sys.exit(app.exec_())
