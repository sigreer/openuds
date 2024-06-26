# -*- coding: utf-8 -*-

#
# Copyright (c) 2024 Virtual Cable S.L.U.
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
import pickle
import typing

from uds.core.environment import Environment
from uds.core import types

# We use storage, so we need transactional tests
from tests.utils.test import UDSTransactionTestCase

from . import fixtures

from uds.services.Xen.deployment import OldOperation, XenLinkedUserService as Deployment

TEST_QUEUE_OLD: typing.Final[list[OldOperation]] = [
    OldOperation.CREATE,
    OldOperation.REMOVE,
    OldOperation.RETRY,
]

TEST_QUEUE: typing.Final[list[types.services.Operation]] = [i.as_operation() for i in TEST_QUEUE_OLD]

SERIALIZED_DEPLOYMENT_DATA: typing.Final[typing.Mapping[str, bytes]] = {
    'v1': b'v1\x01name\x01ip\x01mac\x01vmid\x01reason\x01'
    + pickle.dumps(TEST_QUEUE_OLD, protocol=0)
    + b'\x01task',
}

LAST_VERSION: typing.Final[str] = sorted(SERIALIZED_DEPLOYMENT_DATA.keys(), reverse=True)[0]


class XenDeploymentSerializationTest(UDSTransactionTestCase):
    def check(self, version: str, instance: Deployment) -> None:
        self.assertEqual(instance._name, 'name')
        self.assertEqual(instance._ip, 'ip')
        self.assertEqual(instance._mac, 'mac')
        self.assertEqual(instance._task, 'task')
        self.assertEqual(instance._vmid, 'vmid')
        self.assertEqual(instance._reason, 'reason')
        self.assertEqual(instance._queue, TEST_QUEUE)

    def test_marshaling(self) -> None:
        # queue is kept on "storage", so we need always same environment
        environment = Environment.testing_environment()

        def _create_instance(unmarshal_data: 'bytes|None' = None) -> Deployment:
            instance = Deployment(environment=environment, service=None)  # type: ignore  # service is not used
            if unmarshal_data:
                instance.unmarshal(unmarshal_data)
            return instance

        for v in range(1, len(SERIALIZED_DEPLOYMENT_DATA) + 1):
            version = f'v{v}'
            instance = _create_instance(SERIALIZED_DEPLOYMENT_DATA[version])
            self.check(version, instance)
            # Ensure remarshalled flag is set
            self.assertTrue(instance.needs_upgrade())
            instance.mark_for_upgrade(False)  # reset flag

            marshaled_data = instance.marshal()
            self.assertFalse(
                marshaled_data.startswith(b'\v')
            )  # Ensure fields has been marshalled using new format

            instance = _create_instance(marshaled_data)
            self.assertFalse(
                instance.needs_upgrade()
            )  # Reunmarshall again and check that remarshalled flag is not set
            self.check(version, instance)

    def test_marshaling_queue(self) -> None:
        # queue is kept on "storage", so we need always same environment
        environment = Environment.testing_environment()
        # Store queue
        environment.storage.save_pickled('queue', TEST_QUEUE_OLD)

        def _create_instance(unmarshal_data: 'bytes|None' = None) -> Deployment:
            instance = fixtures.create_userservice_linked()
            if unmarshal_data:
                instance.unmarshal(unmarshal_data)
            return instance

        instance = _create_instance(SERIALIZED_DEPLOYMENT_DATA[LAST_VERSION])
        self.assertEqual(instance._queue, TEST_QUEUE)

        instance._queue = [
            types.services.Operation.CREATE,
            types.services.Operation.FINISH,
        ]
        marshaled_data = instance.marshal()

        instance = _create_instance(marshaled_data)
        self.assertEqual(
            instance._queue,
            [types.services.Operation.CREATE, types.services.Operation.FINISH],
        )
        # Append something remarshall and check
        instance._queue.insert(0, types.services.Operation.RETRY)
        marshaled_data = instance.marshal()
        instance = _create_instance(marshaled_data)
        self.assertEqual(
            instance._queue,
            [
                types.services.Operation.RETRY,
                types.services.Operation.CREATE,
                types.services.Operation.FINISH,
            ],
        )
        # Remove something remarshall and check
        instance._queue.pop(0)
        marshaled_data = instance.marshal()
        instance = _create_instance(marshaled_data)
        self.assertEqual(
            instance._queue,
            [types.services.Operation.CREATE, types.services.Operation.FINISH],
        )
