# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Virtual Cable S.L.U.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L.U. nor the names of its contributors
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
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import logging

from uds.core.ui import gui
from uds.core import transports

from . import _migrator

logger = logging.getLogger(__name__)


# Copy for migration
class TRDPTransport(transports.Transport):
    """
    Provides access via RDP to service.
    This transport can use an domain. If username processed by authenticator contains '@', it will split it and left-@-part will be username, and right password
    """

    typeType = 'TSRDPTransport'

    tunnelServer = gui.TextField()
    tunnelWait = gui.NumericField(defvalue='60')
    verifyCertificate = gui.CheckBoxField(defvalue=gui.FALSE)
    useEmptyCreds = gui.CheckBoxField()
    fixedName = gui.TextField()
    fixedPassword = gui.PasswordField()
    withoutDomain = gui.CheckBoxField()
    fixedDomain = gui.TextField()
    allowSmartcards = gui.CheckBoxField()
    allowPrinters = gui.CheckBoxField()
    allowDrives = gui.ChoiceField(defvalue='false')
    enforceDrives = gui.TextField()
    allowSerials = gui.CheckBoxField()
    allowClipboard = gui.CheckBoxField(defvalue=gui.TRUE)
    allowAudio = gui.CheckBoxField(defvalue=gui.TRUE)
    allowWebcam = gui.CheckBoxField(defvalue=gui.FALSE)
    usbRedirection = gui.ChoiceField(defvalue='false')
    credssp = gui.CheckBoxField(defvalue=gui.TRUE)
    rdpPort = gui.NumericField(defvalue='3389')
    screenSize = gui.ChoiceField(defvalue='-1x-1')
    colorDepth = gui.ChoiceField(defvalue='24')
    wallpaper = gui.CheckBoxField()
    multimon = gui.CheckBoxField()
    aero = gui.CheckBoxField()
    smooth = gui.CheckBoxField(defvalue=gui.TRUE)
    showConnectionBar = gui.CheckBoxField(defvalue=gui.TRUE)
    multimedia = gui.CheckBoxField()
    alsa = gui.CheckBoxField()
    printerString = gui.TextField()
    smartcardString = gui.TextField()
    customParameters = gui.TextField()
    allowMacMSRDC = gui.CheckBoxField(defvalue=gui.FALSE)
    customParametersMAC = gui.TextField()
    customParametersWindows = gui.TextField()
    optimizeTeams = gui.CheckBoxField()

    # This value is the new "tunnel server"
    # Old guacamoleserver value will be stored also on database, but will be ignored
    tunnel = gui.ChoiceField()


def migrate(apps, schema_editor) -> None:
    _migrator.tunnel_transport(apps, TRDPTransport, 'tunnelServer', is_html_server=False)


def rollback(apps, schema_editor) -> None:
    _migrator.tunnel_transport_back(apps, TRDPTransport, 'tunnelServer', is_html_server=False)