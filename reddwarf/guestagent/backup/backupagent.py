# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import logging
from reddwarf.backup.models import DBBackup, BackupState
from reddwarf.common import cfg
from reddwarf.guestagent.dbaas import ADMIN_USER_NAME
from reddwarf.guestagent.dbaas import get_auth_password
from reddwarf.guestagent.strategies.backup.base import \
    BackupError, UnknownBackupType
from reddwarf.guestagent.strategies.storage import get_storage_strategy
from reddwarf.guestagent.strategies.backup import get_backup_strategy
from reddwarf.guestagent.strategies.restore import get_restore_strategy

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

RUNNER = get_backup_strategy(CONF.backup_strategy,
                             CONF.backup_namespace)
BACKUP_CONTAINER = CONF.backup_swift_container


class BackupAgent(object):
    def execute_backup(self, context, backup_id, runner=RUNNER):
        LOG.debug("Searching for backup instance %s", backup_id)
        backup = DBBackup.find_by(id=backup_id)
        LOG.info("Setting task state to %s for instance %s",
                 BackupState.NEW, backup.instance_id)
        backup.state = BackupState.NEW
        backup.save()

        LOG.info("Running backup %s", backup_id)
        user = ADMIN_USER_NAME
        password = get_auth_password()
        swiftStorage = get_storage_strategy(
            CONF.storage_strategy,
            CONF.storage_namespace)(context)

        with runner(filename=backup_id, user=user, password=password) as bkup:
            LOG.info("Starting Backup %s", backup_id)
            success, note, checksum, location = swiftStorage.save(
                BACKUP_CONTAINER,
                bkup)

        LOG.info("Backup %s completed status: %s", backup_id, success)
        LOG.info("Backup %s file size: %s", backup_id, bkup.content_length)
        LOG.info('Backup %s file checksum: %s', backup_id, checksum)
        LOG.info('Backup %s location: %s', backup_id, location)

        LOG.info("Saving %s Backup Info to model", backup_id)
        backup.state = BackupState.COMPLETED if success else BackupState.FAILED
        backup.checksum = checksum
        backup.location = location
        backup.note = note
        backup.backup_type = bkup.backup_type
        backup.save()

        if not success:
            raise BackupError(backup.note)

    def execute_restore(self, context, backup_id):
        LOG.debug("Searching for backup instance %s", backup_id)
        backup = DBBackup.find_by(id=backup_id)
        storage_url = "/".join(backup.location.split('/')[:-2])
        container = backup.location.split('/')[-2]
        filename = backup.location.split('/')[-1]

        restore_runner = self._get_restore_runner(backup.backup_type)

        swift_storage = get_storage_strategy(
            CONF.storage_strategy,
            CONF.storage_namespace)(context)

        download_stream = swift_storage.load(context,
                                             storage_url,
                                             container,
                                             filename)

        with restore_runner(restore_stream=download_stream,
                            restore_location="/var/lib/mysql") as restore:
            pass

        # Prepare step still needs to be run, if needed.

    def _get_restore_runner(self, backup_type):
        """Returns the RestoreRunner associated with this backup type."""
        try:
            runner = get_restore_strategy(backup_type, CONF.restore_namespace)
        except ImportError:
            raise UnknownBackupType("Unknown Backup type: %s" % backup_type)
        return runner
