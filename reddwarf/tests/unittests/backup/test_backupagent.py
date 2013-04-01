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


import hashlib
from mock import patch
from mockito import when, verify, unstub, mock
from reddwarf.backup.models import DBBackup
from reddwarf.backup.models import BackupState
from reddwarf.backup.runner import BackupRunner
from reddwarf.common.exception import ModelNotFoundError
from reddwarf.db.models import DatabaseModelBase
from reddwarf.guestagent.backup import backupagent
import swiftclient.client
import testtools
from webob.exc import HTTPNotFound

def create_fake_data():
    from random import choice
    from string import ascii_letters
    return ''.join([choice(ascii_letters) for _ in xrange(1024)])

class MockBackup(BackupRunner):
    """Create a large temporary file to 'backup' with subprocess."""

    backup_type = 'mock_backup'

    def __init__(self, *args, **kwargs):
        self.data = create_fake_data()
        self.cmd = 'echo %s' % self.data
        super(MockBackup, self).__init__(*args, **kwargs)


class MockSwift(object):
    """Store files in String"""
    def __init__(self, *args, **kwargs):
        self.store = ''
        self.containers = []
        self.url = 'http://mock.swift/user'
        self.etag = hashlib.md5()
    def put_container(self, container):
        if container not in self.containers:
            self.containers.append(container)
        return None
    def put_object(self, container, obj, contents, **kwargs):
        if container not in self.containers:
            raise HTTPNotFound
        while True:
            if not hasattr(contents, 'read'):
                break
            content = contents.read(2 ** 16)
            if not content:
                break
            self.store += content
        self.etag.update(self.store)
        return self.etag.hexdigest()

BACKUP_NS = 'reddwarf.guestagent.strategies.backup'


class BackupAgentTest(testtools.TestCase):

    def tearDown(self):
        super(BackupAgentTest, self).tearDown()
        unstub()

    @patch('reddwarf.guestagent.backup.backupagent.get_auth_password')
    @patch('reddwarf.guestagent.backup.backupagent.create_swift_client',
           MockSwift)
    def test_execute_backup(self, *args):
        """This test should ensure backup agent
                ensures that backup and storage is not running
                resolves backup instance
                starts backup
                starts storage
                reports status
        """
        backup = mock(DBBackup)
        when(DatabaseModelBase).find_by(id='123').thenReturn(backup)
        when(backup).save().thenReturn(backup)

        agent = backupagent.BackupAgent()
        agent.execute_backup(context=None, backup_id='123', runner=MockBackup)

        verify(DatabaseModelBase).find_by(id='123')
        verify(backup).state(BackupState.COMPLETED)
        verify(backup).location = 'http://mock.swift/user/z_CLOUDDB_BACKUPS/123'
        verify(backup, times=2).save()

    def test_execute_backup_model_exception(self):
        """This test should ensure backup agent
                properly handles condition where backup model is not found
        """
        when(DatabaseModelBase).find_by(id='123').thenRaise(ModelNotFoundError)

        agent = backupagent.BackupAgent()
        # probably should catch this exception and return a backup exception
        # also note that since the model is not found there is no way to report
        # this error
        self.assertRaises(ModelNotFoundError, agent.execute_backup,
                          context=None, backup_id='123')
