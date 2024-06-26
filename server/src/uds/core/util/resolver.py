# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2021 Virtual Cable S.L.U.
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
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import typing
import collections.abc

import dns.resolver
import dns.reversename

from uds.core.util.decorators import cached

@cached(prefix='resolver.resolve', timeout=60)  # Cache for 1 hour
def resolve(hostname: str, rdtype: typing.Optional[str] = None) -> list[str]:
    """
    Resolves a hostname to a list of ips
    First items are ipv4, then ipv6
    """
    ips: list[str] = []
    if rdtype is None:
        for i in ('A', 'AAAA'):
            try:
                ips.extend([str(ip) for ip in typing.cast(collections.abc.Iterable[typing.Any], dns.resolver.resolve(hostname, i))])
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
    else:
        try:
            ips.extend([str(ip) for ip in typing.cast(collections.abc.Iterable[typing.Any], dns.resolver.resolve(hostname, rdtype))])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):  # Ignore NoAnswer, that is, the record does not exists
            pass
    return ips

@cached(prefix='resolver.reverse', timeout=60)  # Cache for 1 hour
def reverse_resolve(ip: str) -> list[str]:
    """
    Resolves an ip to a list of hostnames
    """
    try:
        return[str(i).rstrip('.') for i in typing.cast(collections.abc.Iterable[typing.Any], dns.resolver.query(dns.reversename.from_address(ip).to_text(), 'PTR'))]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
