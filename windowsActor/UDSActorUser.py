# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Virtual Cable S.L.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
@author: Adolfo Gómez, dkmaster at dkmon dot com
'''
from __future__ import unicode_literals

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
from udsactor import ipc
from udsactor.log import logger


class MessagesProcessor(QtCore.QThread):

    logoff = QtCore.pyqtSignal(name='logoff')
    displayMessage = QtCore.pyqtSignal(QtCore.QString, name='displayMessage')
    script = QtCore.pyqtSignal(QtCore.QString, name='script')

    def __init__(self):
        super(self.__class__, self).__init__()
        self.ipc = ipc.ClientIPC(39188)
        self.ipc.start()
        self.running = False

    def stop(self):
        self.running = False
        self.ipc.stop()

    def run(self):
        self.running = True
        while self.running:
            msgId, data = self.ipc.getMessage()
            if msgId == ipc.MSG_MESSAGE:
                self.displayMessage.emit(QtCore.QString.fromUtf8(data))
            elif msgId == ipc.MSG_LOGOFF:
                self.logoff.emit()
            elif msgId == ipc.MSG_SCRIPT:
                self.script.emit(QtCore.QString.fromUtf8(data))


class SystemTrayIconApp(QtGui.QSystemTrayIcon):
    def __init__(self, icon, app, parent=None):
        self.app = app
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtGui.QMenu(parent)
        exitAction = self.menu.addAction("Exit")
        exitAction.triggered.connect(self.quit)
        self.setContextMenu(self.menu)
        self.ipc = MessagesProcessor()
        self.ipc.start()

        self.ipc.displayMessage.connect(self.displayMessage, QtCore.Qt.QueuedConnection)

        self.counter = 0

    @QtCore.pyqtSlot(QtCore.QString)
    def displayMessage(self, message):
        self.counter += 1
        print "3.-", message.toUtf8(), '--', self.counter

    def quit(self):
        self.ipc.stop()

        self.app.quit()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
        QtGui.QMessageBox.critical(None, "Systray",
                                   "I couldn't detect any system tray on this system.")
        sys.exit(1)

    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_DesktopIcon))
    trayIcon = SystemTrayIconApp(icon, app)

    trayIcon.show()
    sys.exit(app.exec_())
