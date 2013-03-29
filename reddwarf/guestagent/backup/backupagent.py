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
from eventlet.green import time
from reddwarf.common.exception import PollTimeOut
from reddwarf.common.utils import poll_until
import reddwarf
from reddwarf.backup.models import DBBackup, BackupState

LOG = logging.getLogger(__name__)


class BackupAgent(object):
    def _update_backup_status(self, backup_id, new_state):
        LOG.debug("Searching for backup instance %s", backup_id)
        backup = DBBackup.find_by(id=backup_id)
        LOG.info("Setting task state to %s for instance %s",
                 new_state, backup.instance_id)
        backup.state(new_state)
        backup.save()

    def execute_backup(self, backup_id):
        """
        Main entry point for executing a backup which will create the backup
        data and store it a configurable repository
        :param backup_id: the id for the persistent backup object
        """
        self._update_backup_status(backup_id, BackupState.BUILDING)

        LOG.info("Starting backup process")
        backup = reddwarf.guestagent.strategy.Strategy.get_strategy(
            'innobackupex', 'reddwarf.guestagent.strategies.backup')
        cookie = backup.create_backup(None, 'location', 'output')
        LOG.info("Waiting for backup completion")
        try:
            poll_until(lambda: backup.check_backup_state(None, cookie),
                       lambda status: status == 'COMPLETE', sleep_time=.25,
                       time_out=60)
        except PollTimeOut as pto:
            LOG.exception("Timeout waiting for backup %s", pto)
            self._update_backup_status(backup_id, BackupState.FAILED)
