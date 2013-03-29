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

from mockito import when, verify, unstub, mock, any
from reddwarf.guestagent.strategies.backup.base import BackupStrategy
from reddwarf.guestagent import strategy
from reddwarf.backup.models import DBBackup
from reddwarf.backup.models import BackupState
from reddwarf.common.exception import ModelNotFoundError, PollTimeOut
from reddwarf.db.models import DatabaseModelBase
from reddwarf.guestagent.backup import backupagent
import testtools

BACKUP_NS = 'reddwarf.guestagent.strategies.backup'


class BackupAgentTest(testtools.TestCase):

    def tearDown(self):
        super(BackupAgentTest, self).tearDown()
        unstub()

    def test_execute_backup(self):
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
        mock_strat = mock(BackupStrategy)
        when(strategy.Strategy).get_strategy('innobackupex',
                                             BACKUP_NS).thenReturn(mock_strat)
        when(mock_strat).create_backup(any(), any(), any()).thenReturn(
            'fake_cookie')
        when(mock_strat).check_backup_state(any(), 'fake_cookie').thenReturn(
            'BUILDING').thenReturn('BUILDING').thenReturn('COMPLETE')
        # invocation
        agent = backupagent.BackupAgent()
        agent.execute_backup(backup_id='123')
        # verification
        verify(DatabaseModelBase).find_by(id='123')
        verify(backup).state(BackupState.BUILDING)
        verify(backup).save()
        verify(strategy.Strategy).get_strategy('innobackupex', BACKUP_NS)
        verify(mock_strat).create_backup(any(), any(), any())
        verify(mock_strat, times=3).check_backup_state(any(), 'fake_cookie')

    def test_execute_backup_exception(self):
        """This test should ensure backup agent
                ensures that backup and storage is not running
                resolves backup instance
                starts backup
                throws exception
                sets status to error
                shuts down backup process
        """
        backup = mock(DBBackup)
        when(DatabaseModelBase).find_by(id='123').thenReturn(backup)
        when(backup).save().thenReturn(backup)
        mock_strat = mock(BackupStrategy)
        when(strategy.Strategy).get_strategy('innobackupex',
                                             BACKUP_NS).thenReturn(mock_strat)
        when(mock_strat).create_backup(any(), any(), any()).thenReturn(
            'fake_cookie')
        when(mock_strat).check_backup_state(any(), 'fake_cookie').thenReturn(
            'BUILDING').thenReturn('BUILDING').thenRaise(PollTimeOut)
        # invocation
        agent = backupagent.BackupAgent()
        agent.execute_backup(backup_id='123')
        # verification
        verify(DatabaseModelBase, times=2).find_by(id='123')
        verify(backup).state(BackupState.FAILED)
        verify(backup, times=2).save()
        verify(strategy.Strategy).get_strategy('innobackupex', BACKUP_NS)
        verify(mock_strat).create_backup(any(), any(), any())
        verify(mock_strat, times=3).check_backup_state(any(), 'fake_cookie')

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
                          backup_id='123')
