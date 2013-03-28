#Copyright 2013 Hewlett-Packard Development Company, L.P.

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import logging
from reddwarf.backup.models import DBBackup, BackupState

LOG = logging.getLogger(__name__)


class BackupAgent(object):

    def execute_backup(self, backup_id, mount_point=None):
        LOG.debug("Searching for backup instance %s", backup_id)
        backup = DBBackup.find_by(id=backup_id)
        LOG.info("Setting task state to %s for instance %s", BackupState.BUILDING,
                 backup.instance_id)
        backup.state(BackupState.BUILDING)
        backup.save()
