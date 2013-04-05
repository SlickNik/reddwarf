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
from io import IOBase


import hashlib
import testtools
from testtools.matchers import Equals, Is
from webob.exc import HTTPNotFound
from mockito import when, verify, unstub, mock

from reddwarf.backup.models import DBBackup
from reddwarf.backup.models import BackupState
from reddwarf.common.exception import ModelNotFoundError
from reddwarf.db.models import DatabaseModelBase
from reddwarf.guestagent.backup import backupagent
from reddwarf.guestagent.backup.runner import BackupRunner
from reddwarf.guestagent.backup.runner import UnknownBackupType


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


class MockLossyBackup(MockBackup):
    """Fake Incomplete writes to swift"""

    def read(self, *args):
        results = super(MockLossyBackup, self).read(*args)
        if results:
            # strip a few chars from the stream
            return results[20:]


class MockSwift(object):
    """Store files in String"""

    def __init__(self, *args, **kwargs):
        self.store = ''
        self.containers = []
        self.url = 'http://mockswift/v1'
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

    def setUp(self):
        super(BackupAgentTest, self).setUp()
        when(backupagent).get_auth_password().thenReturn('secret')
        when(backupagent).create_swift_client(None).thenReturn(MockSwift())

    def tearDown(self):
        super(BackupAgentTest, self).tearDown()
        unstub()

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
        self.assertThat(backup.state, Is(BackupState.COMPLETED))
        self.assertThat(backup.location,
                        Equals('http://mockswift/v1/z_CLOUDDB_BACKUPS/123'))
        verify(backup, times=2).save()

    def test_execute_lossy_backup(self, *args):
        """This test verifies that incomplete writes to swift will fail."""
        backup = mock(DBBackup)
        when(backupagent).get_auth_password().thenReturn('secret')
        when(DatabaseModelBase).find_by(id='123').thenReturn(backup)
        when(backup).save().thenReturn(backup)

        agent = backupagent.BackupAgent()

        self.assertRaises(backupagent.BackupError, agent.execute_backup,
                          context=None, backup_id='123',
                          runner=MockLossyBackup)

        self.assertThat(backup.state, Is(BackupState.FAILED))
        self.assertThat(backup.note,
                        Equals("Error sending data to cloud files!"))
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

    def test_execute_restore(self):
        """This test should ensure backup agent
                resolves backup instance
                determines backup/restore type
                transfers/downloads data and invokes the restore module
                reports status
        """
        backup = mock(DBBackup)
        runner = mock()
        backup.backup_type = 'foo'
        when(DatabaseModelBase).find_by(id='123').thenReturn(backup)
        when(backup).save().thenReturn(backup)

        agent = backupagent.BackupAgent()
        agent.register_restore_runner('foo', runner)
        self.assertRaises(NotImplementedError, agent.execute_restore,
                          context=None, backup_id='123')

    def test_restore_unknown(self):
        backup = mock(DBBackup)
        backup.backup_type = 'foo'
        when(DatabaseModelBase).find_by(id='123').thenReturn(backup)
        when(backup).save().thenReturn(backup)

        agent = backupagent.BackupAgent()
        self.assertRaises(UnknownBackupType, agent.execute_restore,
                          context=None, backup_id='123')
