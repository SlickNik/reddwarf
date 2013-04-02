# Copyright 2013 Rackspace Hosting

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from reddwarf.backup.runner import BackupRunner


class MySQLDump(BackupRunner):

    cmd = '/usr/bin/mysqldump'\
          ' --all-databases'\
          ' --opt'\
          ' --compact'\
          ' -h %(host)s '\
          '--password=%(password)s'\
          ' -u %(user)s'\
          ' | gzip'
    backup_type = 'mysqldump'

    @property
    def manifest(self):
        return '%s.gz' % self.filename


class XTRABackup(BackupRunner):

    cmd = 'xtrabackup'\
          ' --password=%(password)s'\
          ' --user=%(user)s'\
          ' --stream=tar'\
          ' ./'\
          ' | gzip'
    backup_type = 'xtrabackup'

    @property
    def manifest(self):
        return '%s.tar.gz' % self.filename