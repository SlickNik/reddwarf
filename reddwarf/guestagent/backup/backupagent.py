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
from reddwarf.common import utils
from reddwarf.guestagent.dbaas import ADMIN_USER_NAME
from reddwarf.guestagent.dbaas import get_auth_password
from reddwarf.guestagent.backup.runner import BackupError
from reddwarf.guestagent.backup.runner import UnknownBackupType
from reddwarf.common.remote import create_swift_client

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

RUNNER = utils.import_class(CONF.backup_runner)
BACKUP_CONTAINER = CONF.backup_swift_container


class BackupAgent(object):

    def __init__(self):
        self._restore_runners = {}

    def register_restore_runner(self, name, kls):
        """Register a new restore runner"""
        self._restore_runners[name] = kls

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
        connection = create_swift_client(context)
        with runner(filename=backup_id, user=user, password=password) as bkup:
            LOG.info("Starting Backup %s", backup_id)
            connection.put_container(BACKUP_CONTAINER)
            while not bkup.end_of_file:
                segment = bkup.segment
                etag = connection.put_object(BACKUP_CONTAINER, segment, bkup)
                # Check each segment MD5 hash against swift etag
                # Raise an error and mark backup as failed
                if etag != bkup.schecksum.hexdigest():
                    print etag, bkup.schecksum.hexdigest()
                    backup.state = BackupState.FAILED
                    backup.note = "Error sending data to cloud files!"
                    backup.save()
                    raise BackupError(backup.note)

            checksum = bkup.checksum.hexdigest()
            url = connection.url
            location = "%s/%s/%s" % (url, BACKUP_CONTAINER, bkup.manifest)
            LOG.info("Backup %s file size: %s", backup_id, bkup.content_length)
            LOG.info('Backup %s file checksum: %s', backup_id, checksum)
            LOG.info('Backup %s location: %s', backup_id, location)
            # Create the manifest file
            headers = {'X-Object-Manifest': bkup.prefix}
            connection.put_object(BACKUP_CONTAINER,
                                  bkup.manifest,
                                  contents='',
                                  headers=headers)
            LOG.info("Saving %s Backup Info", backup_id)
            backup.state = BackupState.COMPLETED
            backup.checksum = checksum
            backup.location = location
            backup.backup_type = bkup.backup_type
            backup.save()

    def execute_restore(self, context, backup_id):
        backup = DBBackup.find_by(id=backup_id)
        restore_runner = self._get_restore_runner(backup.backup_type)
        raise NotImplementedError('execute restore is not yet implemented')

    def _get_restore_runner(self, backup_type):
        """Returns the RestoreRunner associated with this backup type."""
        runner = self._restore_runners.get(backup_type)
        if runner is None:
            raise UnknownBackupType("Unknown Backup type: %s" % backup_type)
        return runner
