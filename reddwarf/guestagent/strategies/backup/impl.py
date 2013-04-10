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

from reddwarf.guestagent.strategies.backup import base
from reddwarf.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class MySQLDump(base.BackupRunner):
    """ Implementation of Backup Strategy for MySQLDump """
    __strategy_name__ = 'mysqldump'

    cmd = '/usr/bin/mysqldump'\
          ' --all-databases'\
          ' --opt'\
          ' --compact'\
          ' -h %(host)s '\
          '--password=%(password)s'\
          ' -u %(user)s'\
          ' | gzip'

    @property
    def manifest(self):
        return '%s.gz' % self.filename


class InnoBackupEx(base.BackupRunner):
    """ Implementation of Backup Strategy for InnoBackupEx """
    __strategy_name__ = 'innobackupex'

    cmd = 'sudo innobackupex'\
          ' --stream=xbstream'\
          ' /var/lib/mysql 2>/tmp/innobackupex.log | gzip'

    @property
    def manifest(self):
        return '%s.xbstream.gz' % self.filename
