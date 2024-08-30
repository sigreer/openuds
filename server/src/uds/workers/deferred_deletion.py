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
import dataclasses
import collections.abc
import datetime
import typing
import logging

from uds.models import Service
from uds.core.util.model import sql_now
from uds.core.jobs import Job
from uds.core.util import storage, utils
from uds.core.consts import deferred_deletion as consts
from uds.core.types import deferred_deletion as types

from uds.core.services.generics import exceptions as gen_exceptions

if typing.TYPE_CHECKING:
    from uds.core.services.generics.dynamic.service import DynamicService

logger = logging.getLogger(__name__)


def execution_timer() -> 'utils.ExecutionTimer':
    """
    Generates an execution timer for deletion operations
    This allows to delay the next check based on how long the operation took
    """
    return utils.ExecutionTimer(
        delay_threshold=consts.OPERATION_DELAY_THRESHOLD, max_delay_rate=consts.MAX_DELAY_RATE
    )


def next_execution_calculator(*, fatal: bool = False, delay_rate: float = 1.0) -> datetime.datetime:
    """
    Returns the next check time for a deletion operation
    """
    return sql_now() + (
        consts.CHECK_INTERVAL * (consts.FATAL_ERROR_INTERVAL_MULTIPLIER if fatal else 1) * delay_rate
    )


@dataclasses.dataclass
class DeletionInfo:
    vmid: str
    created: datetime.datetime
    next_check: datetime.datetime
    service_uuid: str  # uuid of the service that owns this vmid (not the pool, but the service)
    fatal_retries: int = 0  # Fatal error retries
    total_retries: int = 0  # Total retries
    retries: int = 0  # Retries to stop again or to delete again in STOPPING_GROUP or DELETING_GROUP

    deferred_storage: typing.ClassVar[storage.Storage] = storage.Storage('deferdel_worker')

    @property
    def key(self) -> str:
        return DeletionInfo.generate_key(self.service_uuid, self.vmid)

    def sync_to_storage(self, group: types.DeferredStorageGroup) -> None:
        """
        Ensures that this object is stored on the storage
        If exists, it will be updated, if not, it will be created
        """
        with DeletionInfo.deferred_storage.as_dict(group, atomic=True) as storage_dict:
            storage_dict[self.key] = self

    # For reporting
    def as_csv(self) -> str:
        return f'{self.vmid},{self.created},{self.next_check},{self.service_uuid},{self.fatal_retries},{self.total_retries},{self.retries}'

    @staticmethod
    def generate_key(service_uuid: str, vmid: str) -> str:
        return f'{service_uuid}_{vmid}'

    @staticmethod
    def create_on_storage(group: str, vmid: str, service_uuid: str, delay_rate: float = 1.0) -> None:
        with DeletionInfo.deferred_storage.as_dict(group, atomic=True) as storage_dict:
            storage_dict[DeletionInfo.generate_key(service_uuid, vmid)] = DeletionInfo(
                vmid=vmid,
                created=sql_now(),
                next_check=next_execution_calculator(delay_rate=delay_rate),
                service_uuid=service_uuid,
                # fatal, total an retries are 0 by default
            )

    @staticmethod
    def get_from_storage(
        group: types.DeferredStorageGroup,
    ) -> tuple[dict[str, 'DynamicService'], list['DeletionInfo']]:
        """
        Get a list of objects to be processed from storage

        Note:
            This method will remove the objects from storage, so if needed, has to be readded
            This is so we can release locks as soon as possible
        """
        count = 0
        infos: list[DeletionInfo] = []

        services: dict[str, 'DynamicService'] = {}

        # First, get ownership of to_delete objects to be processed
        # We do this way to release db locks as soon as possible
        now = sql_now()
        with DeletionInfo.deferred_storage.as_dict(group, atomic=True) as storage_dict:
            for key, info in sorted(
                typing.cast(collections.abc.Iterable[tuple[str, DeletionInfo]], storage_dict.items()),
                key=lambda x: x[1].next_check,
            ):
                # if max retries reached, remove it
                if info.total_retries >= consts.MAX_RETRAYABLE_ERROR_RETRIES:
                    logger.error(
                        'Too many retries deleting %s from service %s, removing from deferred deletion',
                        info.vmid,
                        info.service_uuid,
                    )
                    del storage_dict[key]
                    continue

                if info.next_check > now:  # If not time to process yet, skip
                    continue
                try:
                    if info.service_uuid not in services:
                        services[info.service_uuid] = typing.cast(
                            'DynamicService', Service.objects.get(uuid=info.service_uuid).get_instance()
                        )
                except Exception as e:
                    logger.error('Could not get service instance for %s: %s', info.service_uuid, e)
                    del storage_dict[key]
                    continue

                if (count := count + 1) > consts.MAX_DELETIONS_AT_ONCE:
                    break

                del storage_dict[key]  # Remove from storage, being processed

                # Only add if not too many retries already
                infos.append(info)
        return services, infos

    @staticmethod
    def count_from_storage(group: types.DeferredStorageGroup) -> int:
        # Counts the total number of objects in storage
        with DeletionInfo.deferred_storage.as_dict(group) as storage_dict:
            return len(storage_dict)

    @staticmethod
    def csv_header() -> str:
        return 'vmid,created,next_check,service_uuid,fatal_retries,total_retries,retries'


class DeferredDeletionWorker(Job):
    frecuency = 7  # Frequency for this job, in seconds
    friendly_name = 'Deferred deletion runner'

    @staticmethod
    def add(service: 'DynamicService', vmid: str, execute_later: bool = False) -> None:
        logger.debug('Adding %s from service %s to deferred deletion', vmid, service.type_name)
        # If sync, execute now
        if not execute_later:
            exec_time = execution_timer()
            try:
                with exec_time:
                    if service.must_stop_before_deletion:
                        if service.is_running(None, vmid):
                            if service.should_try_soft_shutdown():
                                service.shutdown(None, vmid)
                            else:
                                service.stop(None, vmid)
                            DeletionInfo.create_on_storage(
                                types.DeferredStorageGroup.STOPPING, vmid, service.db_obj().uuid
                            )
                            return

                    service.execute_delete(vmid)
                # If this takes too long, we will delay the next check a bit
                DeletionInfo.create_on_storage(
                    types.DeferredStorageGroup.DELETING,
                    vmid,
                    service.db_obj().uuid,
                    delay_rate=exec_time.delay_rate,
                )
            except gen_exceptions.NotFoundError:
                return  # Already removed
            except Exception as e:
                logger.warning(
                    'Could not delete %s from service %s: %s. Retrying later.', vmid, service.db_obj().name, e
                )
                DeletionInfo.create_on_storage(
                    types.DeferredStorageGroup.TO_DELETE,
                    vmid,
                    service.db_obj().uuid,
                    delay_rate=exec_time.delay_rate,
                )
                return
        else:
            if service.must_stop_before_deletion:
                DeletionInfo.create_on_storage(types.DeferredStorageGroup.TO_STOP, vmid, service.db_obj().uuid)
            else:
                DeletionInfo.create_on_storage(
                    types.DeferredStorageGroup.TO_DELETE, vmid, service.db_obj().uuid
                )
            return

    def _process_exception(
        self,
        info: DeletionInfo,
        to_group: types.DeferredStorageGroup,
        services: dict[str, 'DynamicService'],
        e: Exception,
        *,
        delay_rate: float = 1.0,
    ) -> None:
        if isinstance(e, gen_exceptions.NotFoundError):
            return  # All ok, already removed

        is_retryable = isinstance(e, gen_exceptions.RetryableError)
        logger.error(
            'Error deleting %s from service %s: %s%s',
            info.vmid,
            services[info.service_uuid].db_obj().name,
            e,
            ' (will retry)' if is_retryable else '',
        )

        if not is_retryable:
            info.next_check = next_execution_calculator(fatal=True, delay_rate=delay_rate)
            info.fatal_retries += 1
            if info.fatal_retries >= consts.MAX_FATAL_ERROR_RETRIES:
                logger.error(
                    'Fatal error deleting %s from service %s, removing from deferred deletion',
                    info.vmid,
                    services[info.service_uuid].db_obj().name,
                )
                return  # Do not readd it
        info.next_check = next_execution_calculator(delay_rate=delay_rate)
        info.total_retries += 1
        if info.total_retries >= consts.MAX_RETRAYABLE_ERROR_RETRIES:
            logger.error(
                'Too many retries deleting %s from service %s, removing from deferred deletion',
                info.vmid,
                services[info.service_uuid].db_obj().name,
            )
            return  # Do not readd it
        info.sync_to_storage(to_group)

    def process_to_stop(self) -> None:
        services, to_stop = DeletionInfo.get_from_storage(types.DeferredStorageGroup.TO_STOP)
        logger.debug('Processing %s to stop', to_stop)

        # Now process waiting stops
        for info in to_stop:  # Key not used
            exec_time = execution_timer()
            try:
                service = services[info.service_uuid]
                with exec_time:
                    if service.is_running(None, info.vmid):
                        # if info.retries < RETRIES_TO_RETRY, means this is the first time we try to stop it
                        if info.retries < consts.RETRIES_TO_RETRY:
                            if service.should_try_soft_shutdown():
                                service.shutdown(None, info.vmid)
                            else:
                                service.stop(None, info.vmid)
                            info.fatal_retries = info.total_retries = 0
                        else:
                            info.total_retries += 1  # Count this as a general retry
                            info.retries = 0  # Reset retries
                            service.stop(None, info.vmid)  # Always try to stop it if we have tried before

                        info.next_check = next_execution_calculator(delay_rate=exec_time.delay_rate)
                        info.sync_to_storage(types.DeferredStorageGroup.STOPPING)
                    else:
                        # Do not update last_check to shutdown it asap, was not running after all
                        info.sync_to_storage(types.DeferredStorageGroup.TO_DELETE)
            except Exception as e:
                self._process_exception(
                    info, types.DeferredStorageGroup.TO_STOP, services, e, delay_rate=exec_time.delay_rate
                )

    def process_stopping(self) -> None:
        services, stopping = DeletionInfo.get_from_storage(types.DeferredStorageGroup.STOPPING)
        logger.debug('Processing %s stopping', stopping)

        # Now process waiting for finishing stops
        for info in stopping:
            exec_time = execution_timer()
            try:
                info.retries += 1
                if info.retries > consts.RETRIES_TO_RETRY:
                    # If we have tried to stop it, and it has not stopped, add to stop again
                    info.next_check = next_execution_calculator()
                    info.total_retries += 1
                    info.sync_to_storage(types.DeferredStorageGroup.TO_STOP)
                    continue
                with exec_time:
                    if services[info.service_uuid].is_running(None, info.vmid):
                        info.next_check = next_execution_calculator(delay_rate=exec_time.delay_rate)
                        info.total_retries += 1
                        info.sync_to_storage(types.DeferredStorageGroup.STOPPING)
                    else:
                        info.next_check = next_execution_calculator(delay_rate=exec_time.delay_rate)
                        info.fatal_retries = info.total_retries = 0
                        info.sync_to_storage(types.DeferredStorageGroup.TO_DELETE)
            except Exception as e:
                self._process_exception(
                    info, types.DeferredStorageGroup.STOPPING, services, e, delay_rate=exec_time.delay_rate
                )

    def process_to_delete(self) -> None:
        services, to_delete = DeletionInfo.get_from_storage(types.DeferredStorageGroup.TO_DELETE)
        logger.debug('Processing %s to delete', to_delete)

        # Now process waiting deletions
        for info in to_delete:
            service = services[info.service_uuid]
            exec_time = execution_timer()
            try:
                with exec_time:
                    # If must be stopped before deletion, and is running, put it on to_stop
                    if service.must_stop_before_deletion and service.is_running(None, info.vmid):
                        info.sync_to_storage(types.DeferredStorageGroup.TO_STOP)
                        continue

                    service.execute_delete(info.vmid)
                # And store it for checking later if it has been deleted, reseting counters
                info.next_check = next_execution_calculator(delay_rate=exec_time.delay_rate)
                info.retries = 0
                info.total_retries += 1
                info.sync_to_storage(types.DeferredStorageGroup.DELETING)
            except Exception as e:
                self._process_exception(
                    info,
                    types.DeferredStorageGroup.TO_DELETE,
                    services,
                    e,
                    delay_rate=exec_time.delay_rate,
                )

    def process_deleting(self) -> None:
        """
        Process all deleting objects, and remove them if they are already deleted

        Note: Very similar to process_to_delete, but this one is for objects that are already being deleted
        """
        services, deleting = DeletionInfo.get_from_storage(types.DeferredStorageGroup.DELETING)
        logger.debug('Processing %s deleting', deleting)

        # Now process waiting for finishing deletions
        for info in deleting:  # Key not used
            exec_time = execution_timer()
            try:
                info.retries += 1
                if info.retries > consts.RETRIES_TO_RETRY:
                    # If we have tried to delete it, and it has not been deleted, add to delete again
                    info.next_check = next_execution_calculator()
                    info.total_retries += 1
                    info.sync_to_storage(types.DeferredStorageGroup.TO_DELETE)
                    continue
                with exec_time:
                    # If not finished, readd it for later check
                    if not services[info.service_uuid].is_deleted(info.vmid):
                        info.next_check = next_execution_calculator(delay_rate=exec_time.delay_rate)
                        info.total_retries += 1
                        info.sync_to_storage(types.DeferredStorageGroup.DELETING)
            except Exception as e:
                self._process_exception(
                    info, types.DeferredStorageGroup.DELETING, services, e, delay_rate=exec_time.delay_rate
                )

    def run(self) -> None:
        self.process_to_stop()
        self.process_stopping()
        self.process_to_delete()
        self.process_deleting()

    # To allow reporting what is on the queues
    @staticmethod
    def report(out: typing.TextIO) -> None:
        out.write(DeletionInfo.csv_header() + '\n')
        for group in types.DeferredStorageGroup:
            with DeletionInfo.deferred_storage.as_dict(group) as storage:
                for _key, info in typing.cast(dict[str, DeletionInfo], storage).items():
                    out.write(info.as_csv() + '\n')
        out.write('\n')
