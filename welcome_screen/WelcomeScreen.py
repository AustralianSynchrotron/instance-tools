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
import subprocess
from subprocess import Popen
from sys import platform
from string import Template
import argparse
import urllib2
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


#-----------------------
#     Main classes
#-----------------------
class RaidarItem(QWidget):
    """The shortcut GUI Qt widget.
       It consists of an icon on the left hand side and a title+description on the right hand side."""
    def __init__(self, name, description, icon, cmd=[], shell=False, cwd=None, bkg_colour = [255, 255, 255]):
        QWidget.__init__(self)

        self._cmd = cmd
        self._shell = shell
        self._cwd = cwd

        # Store the background colour and calculate the hover colour from it
        self._bkg_colour = QColor(bkg_colour[0], bkg_colour[1], bkg_colour[2])
        self._bkg_colour_hover = self._bkg_colour.lighter(108)

        self.setPalette(QPalette(self._bkg_colour))
        self.setAutoFillBackground(True)

        cont_layout = QHBoxLayout()
        text_layout = QVBoxLayout()

        icon_label = QLabel(self)
        icon_label.setPixmap(icon)
        cont_layout.addWidget(icon_label)
        cont_layout.addLayout(text_layout)
        cont_layout.addStretch(1)

        name_label = QLabel('<b>'+name+'</b>', self)
        desc_label = QLabel(description, self)
        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)

        self.setLayout(cont_layout)

    def enterEvent(self, event):
        """This event is called when the mouse cursor enters this widget."""
        self.setPalette(QPalette(self._bkg_colour_hover))

    def leaveEvent(self, event):
        """This event is called when the mouse cursor leaves this widget."""
        self.setPalette(QPalette(self._bkg_colour))

    def mousePressEvent(self, event):
        """This event is called when the left mouse button is pressed."""
        if event.button() == Qt.LeftButton:
            Popen(self._cmd, shell=self._shell, cwd=self._cwd)


class RaidarStartScreen(QWidget):
    """The main Raidar start screen window."""

    def add_group(self, container, node, bkg_colour):
        """Adds a group of shortcut widgets to the specified container.
           container - The container widget to which the widgets of the group should be added.
           node - The XML node of the group
           bkg_colour - The background colour of the group's widgets.
        """
        if node == None:
            return

        # White background
        self.setPalette(QPalette(QColor(255, 255, 255)))
        self.setAutoFillBackground(True)

        # Get the name, description and the executable
        name = node.find('name').text
        desc = node.find('description').text
        cmd  = [node.find('executable').text]

        # Check if the shell attribute was set
        shell = False
        if 'shell' in node.find('executable').attrib:
            shell_attrib = node.find('executable').attrib['shell']
            if shell_attrib.upper() == "TRUE":
                shell = True

        # Check if the cwd attribute was set
        cwd = None
        if 'startIn' in node.find('executable').attrib:
            cwd = node.find('executable').attrib['startIn']

        # Fill the arguments
        arg_nodes = node.find('arguments')
        if arg_nodes != None:
            for arg_node in arg_nodes.findall('argument'):
                cmd.append(arg_node.text)

        # Check if the icon exists, if not use a dummy icon
        icon = QPixmap(os.path.join(self._icon_path, 'dummy.png'))
        icon_location = os.path.join(self._icon_path, node.find('icon').text)
        if os.path.exists(icon_location):
            icon = QPixmap(icon_location)

        # Create the widget and add it to the program container
        shortcut_item = RaidarItem(name, desc, icon, cmd, shell, cwd, bkg_colour)
        container.addWidget(shortcut_item)


    def get_greeting_VirtualBox(self):
        guest_prop = Popen(["VBoxControl", "guestproperty", "get", "UserFullName"], stdout=subprocess.PIPE, shell=True)
        gpOut, gpErr = guest_prop.communicate()
        user_fullname = "-"
        for item in gpOut.split("\n"):
            if "Value: " in item:
                user_fullname = ""
                result_split = item.split()
                for iName in range(1, len(result_split)):
                    user_fullname += result_split[iName] + " "
                break
        return user_fullname


    def get_greeting_NeCTAR(self):
        try:
            url = 'http://169.254.169.254/openstack/2012-08-10/meta_data.json'
            req = urllib2.Request(url)
            resp = urllib2.urlopen(req)
            j = json.loads(resp.read())
            return j['meta']['nexel-username']
        except Exception:
            return ""


    def __init__(self, config_filename):
        QWidget.__init__(self)

        # Import XML document
        tree = ET.parse(config_filename)
        root = tree.getroot()

        # Get application settings
        self._node_settings = root.find('settings')
        self._icon_path = os.path.join(os.path.dirname(os.path.abspath(config_filename)),
                                       self._node_settings.find('iconpath').text)

        # Create the layout
        main_layout    = QVBoxLayout()
        content_layout = QHBoxLayout()
        left_layout    = QVBoxLayout()
        right_layout   = QVBoxLayout()
        status_layout  = QHBoxLayout()
        self.setLayout(main_layout)

        # Set title and title logo
        self.setWindowTitle(self._node_settings.find('title').text)
        logo = QPixmap(os.path.join(self._icon_path, self._node_settings.find('logo').text))
        logo_label = QLabel(self)
        logo_label.setPixmap(logo)
        main_layout.addWidget(logo_label, 0, Qt.AlignCenter)

        # Add the welcome [username] label
        greeting_type = self._node_settings.find('greetings').attrib['type']
        greeting_text = ""
        if greeting_type == "Text":
            greeting_text = self._node_settings.find('greetings').text
        elif greeting_type == "VirtualBox":
            templ = Template(self._node_settings.find('greetings').text)
            greeting_text = templ.substitute(username=self.get_greeting_VirtualBox())
        elif greeting_type == "NeCTAR":
            templ = Template(self._node_settings.find('greetings').text)
            greeting_text = templ.substitute(username=self.get_greeting_NeCTAR())
        welcome_label = QLabel(greeting_text, self)
        main_layout.addWidget(welcome_label, 0, Qt.AlignLeft)

        # Add content layout container
        main_layout.addLayout(content_layout)
        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)
        main_layout.addLayout(status_layout)

        # Center application window
        self.setMinimumSize(int(self._node_settings.find('width').text),
                            int(self._node_settings.find('height').text))
        desktop_widget = QApplication.desktop()
        screen_rect = desktop_widget.availableGeometry(self)
        self.move(screen_rect.center() - self.rect().center())

        # Add the different content types
        for group in root.find('content'):
            bkg_colour = map(int, group.attrib['bkgColour'].split(','))

            for shortcut in group.findall('shortcut'):
                if group.attrib['align'] == "left":
                    self.add_group(left_layout, shortcut, bkg_colour)
                else:
                    self.add_group(right_layout, shortcut, bkg_colour)

        left_layout.addStretch(1)
        right_layout.addStretch(1)

        exit_button = QPushButton("close window")
        exit_button.clicked.connect(exit)
        status_layout.addStretch(1)
        status_layout.addWidget(exit_button)


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
    widget = RaidarStartScreen(confPath)
    widget.show()
    sys.exit(app.exec_())
