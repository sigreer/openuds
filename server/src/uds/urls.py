# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Virtual Cable S.L.
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

"""
@author: Adolfo Gómez, dkmaster at dkmon dot com
"""

from django.urls import re_path, path
from django.conf.urls import include
from uds.core.util.modfinder import loadModulesUrls
from django.views.i18n import JavaScriptCatalog
from django.views.generic.base import RedirectView

from uds import REST
import uds.web.views

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('uds',),
}

urlpatterns = [
    # Root url placeholder
    path(r'', RedirectView.as_view(pattern_name='page.index', permanent=False), name='page.index.placeholder'),

    # START COMPAT redirections & urls
    path(r'login/', RedirectView.as_view(pattern_name='page.login', permanent=False), name='page.login.compat'),
    path(r'logout/', RedirectView.as_view(pattern_name='page.logut'), name='page.logout.compat'),

    # Backwards compatibility with REST API path
    re_path(r'^rest/(?P<arguments>.*)$', REST.Dispatcher.as_view(), name="REST.compat"),

    # Old urls for federated authentications
    re_path(r'^auth/(?P<authName>.+)', uds.web.views.authCallback, name='page.auth.callback.compat'),
    re_path(r'^authinfo/(?P<authName>.+)', uds.web.views.authInfo, name='page.auth.info.compat'),

    # Ticket authentication
    re_path(r'^tkauth/(?P<ticketId>.+)$', uds.web.views.ticketAuth, name='page,auth.ticket.compat'),

    # END COMPAT

    # Index
    path(r'uds/page/services/', uds.web.views.modern.index, name='page.index'),

    # Login/logout
    path(r'uds/page/login/', uds.web.views.modern.login, name='page.login'),
    re_path(r'^uds/page/login/(?P<tag>.+)$', uds.web.views.modern.login, name='page.login.tag'),

    path(r'uds/page/logout/', uds.web.views.modern.logout, name='page.logout'),

    # Error URL
    re_path(r'^uds/page/error/(?P<error>.+)$', uds.web.views.error, name='page.error'),

    # Federated authentication
    re_path(r'^uds/page/auth/(?P<authName>[^/]+)$', uds.web.views.authCallback, name='page.auth.callback'),
    re_path(r'^uds/page/auth/info/(?P<authName>.+)$', uds.web.views.authInfo, name='page.auth.info'),

    # Ticket authentication related
    re_path(r'^uds/page/ticket/auth/(?P<ticketId>.+)$', uds.web.views.ticketAuth, name='page.ticket.auth'),
    path(r'uds/page/ticket/launcher', uds.web.views.modern.index, name='page.ticket.launcher'),

    # This must be the last, so any patition will be managed by client in fact
    re_path(r'uds/page/.*', uds.web.views.modern.index, name='page.placeholder'),

    # Utility

    # Javascript
    path(r'uds/utility/uds.js', uds.web.views.modern.js, name="utility.js"),

    # i18n
    re_path(r'^uds/utility/i18n/(?P<lang>[a-z]*).js$', JavaScriptCatalog.as_view(), name='utility.jsCatalog'),
    path(r'uds/utility/i18n/', include('django.conf.urls.i18n')),

    # Dowloader
    re_path(r'^uds/utility/download/(?P<idDownload>[a-zA-Z0-9-]*)$', uds.web.views.download, name='utility.downloader'),

    re_path(r'^uds/utility/files/(?P<uuid>.+)', uds.web.views.file_storage, name='utility.file_storage'),

    # WEB API path (not REST api, frontend)
    re_path(r'^uds/webapi/img/transport/(?P<idTrans>.+)$', uds.web.views.transportIcon, name='webapi.transportIcon'),
    re_path(r'^uds/webapi/img/gallery/(?P<idImage>.+)$', uds.web.views.image, name='webapi.galleryImage'),

    re_path(r'^uds/webapi/enable/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.clientEnabler, name='webapi.enabler'),

    re_path(r'^release/(?P<idService>.+)$', uds.web.views.release, name='webapi.releaser'),
    re_path(r'^reset/(?P<idService>.+)$', uds.web.views.reset, name='webapi.resetter'),

    # Services list, ...
    path(r'uds/webapi/services', uds.web.views.modern.servicesData, name='webapi.services'),

    # Transport own link processor
    re_path(r'^uds/webapi/trans/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.transportOwnLink, name='TransportOwnLink'),
    # Authenticators custom html
    re_path(r'^uds/webapi/customAuth/(?P<idAuth>.*)$', uds.web.views.customAuth, name='uds.web.views.customAuth'),

    # REST Api
    re_path(r'^uds/rest/(?P<arguments>.*)$', REST.Dispatcher.as_view(), name="REST"),

    # Web admin GUI
    re_path(r'^uds/adm/', include('uds.admin.urls')),

    # old part, remove
    # re_path(r'^$', uds.web.views.index, name='uds.web.views.index'),
    # re_path(r'^login/$', uds.web.views.login, name='uds.web.views.login'),
    # re_path(r'^login/(?P<tag>.+)$', uds.web.views.login, name='uds.web.views.login'),
    # re_path(r'^logout$', uds.web.views.logout, name='uds.web.views.logout'),

    # Icons
    # re_path(r'^transicon/(?P<idTrans>.+)$', uds.web.views.transportIcon, name='uds.web.views.transportIcon'),
    # Images
    # re_path(r'^srvimg/(?P<idImage>.+)$', uds.web.views.serviceImage, name='uds.web.views.serviceImage'),
    # re_path(r'^galimg/(?P<idImage>.+)$', uds.web.views.image, name='galleryImage'),
    # Error URL
    # re_path(r'^error/(?P<idError>.+)$', uds.web.views.error, name='uds.web.views.error'),

    # Transport own link processor
    # re_path(r'^trans/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.transportOwnLink, name='TransportOwnLink'),
    # Authenticators custom html
    # re_path(r'^customAuth/(?P<idAuth>.*)$', uds.web.views.customAuth, name='uds.web.views.customAuth'),
    # Preferences
    # re_path(r'^prefs$', uds.web.views.prefs, name='uds.web.views.prefs'),
    # Change Language
    # re_path(r'^i18n/', include('django.conf.urls.i18n')),

    # Downloads
    # re_path(r'^idown/(?P<idDownload>[a-zA-Z0-9-]*)$', uds.web.views.download, name='uds.web.views.download'),

    # downloads for client
    # re_path(r'^down$', uds.web.views.client_downloads, name='uds.web.views.client_downloads'),
    # re_path(r'^down/(?P<os>[a-zA-Z0-9-]*)$', uds.web.views.client_downloads, name='uds.web.views.client_downloads'),
    # re_path(r'^pluginDetection/(?P<detection>[a-zA-Z0-9-]*)$', uds.web.views.plugin_detection, name='PluginDetection'),

    # Client access enabler
    # re_path(r'^enable/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.clientEnabler, name='ClientAccessEnabler'),

    # Releaser
    # re_path(r'^release/(?P<idService>.+)$', uds.web.views.release, name='Releaser'),
    # re_path(r'^reset/(?P<idService>.+)$', uds.web.views.reset, name='Reseter'),

    # Custom authentication callback
    # re_path(r'^auth/(?P<authName>.+)', uds.web.views.authCallback, name='uds.web.views.authCallback'),
    # re_path(r'^authinfo/(?P<authName>.+)', uds.web.views.authInfo, name='uds.web.views.authInfo'),
    # re_path(r'^about', uds.web.views.about, name='uds.web.views.about'),
    # Ticket authentication
    # re_path(r'^tkauth/(?P<ticketId>.+)$', uds.web.views.ticketAuth, name='TicketAuth'),

    # REST Api
    # re_path(r'^rest/(?P<arguments>.*)$', REST.Dispatcher.as_view(), name="REST"),

    # Web admin GUI
    # re_path(r'^adm/', include('uds.admin.urls')),

    # Files
    # re_path(r'^files/(?P<uuid>.+)', uds.web.views.file_storage, name='uds.web.views.file_storage'),

    # Internacionalization in javascript
    # Javascript catalog. In fact, lang is not used, but it is maintanied for "backward" user templates compatibility
    # re_path(r'^jsi18n/(?P<lang>[a-z]*)$', JavaScriptCatalog.as_view(), name='uds.web.views.jsCatalog'),
]

# Append urls from special dispatchers
urlpatterns += loadModulesUrls()
