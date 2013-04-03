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

from mockito import mock, when, unstub, any
import testtools
from reddwarf.common import wsgi
from reddwarf.backup.service import BackupsController
from reddwarf.backup.models import Backup
from reddwarf.common import exception
from reddwarf.instance import models
from reddwarf.backup.models import BackupState
from reddwarf.taskmanager import api


class TestBackupController(testtools.TestCase):
    def setUp(self):
        super(TestBackupController, self).setUp()
        self.controller = BackupsController()

    def tearDown(self):
        super(TestBackupController, self).tearDown()
        unstub()

    def test_create_instance_not_found(self):

        data = {'backup': {'name': 'backup_test',
                           'instance': 'test_instance',
                           'description': 'test desc'}}

        req = mock()
        req.environ = {wsgi.CONTEXT_KEY: 'Context'}
        when(models).get_db_info(any(), any()).thenRaise(exception.NotFound)
        self.assertRaises(exception.NotFound, self.controller.create, req,
                          data, 'tenant 123')

    def test_create_backup_is_running(self):

        data = {'backup': {'name': 'backup_test',
                           'instance': 'test_instance',
                           'description': 'test desc'}}

        available_backup = mock()
        available_backup.state = BackupState.COMPLETED
        failed_backup = mock()
        failed_backup.state = BackupState.FAILED
        building_backup = mock()
        building_backup.state = BackupState.BUILDING
        new_backup = mock()
        new_backup.state = BackupState.NEW

        req = mock()
        req.environ = {wsgi.CONTEXT_KEY: 'Context'}
        when(models).get_db_info(any(), any()).thenReturn(None)
        when(Backup).list_for_instance(any()).thenReturn([available_backup,
                                                          failed_backup,
                                                          building_backup])
        self.assertRaises(exception.BackupAlreadyRunning,
                          self.controller.create, req, data, 'tenant 123')

    def test_create(self):

        backup = mock()
        backup.id = 'backup_id'
        backup.name = 'backup_test',
        backup.description = 'test desc'
        backup.location = 'test location'
        backup.instance_id = 'instance id'
        backup.created = 'yesterday'
        backup.updated = 'today'
        backup.state = BackupState.NEW

        data = {'backup': {'name': backup.name,
                           'instance': backup.instance_id,
                           'description': backup.description}}

        available_backup = mock()
        available_backup.state = BackupState.COMPLETED
        failed_backup = mock()
        failed_backup.state = BackupState.FAILED
        building_backup = mock()
        building_backup.state = BackupState.BUILDING
        new_backup = mock()
        new_backup.state = BackupState.NEW

        req = mock()
        req.environ = {wsgi.CONTEXT_KEY: 'Context'}
        when(models).get_db_info(any(), any()).thenReturn(None)
        when(Backup).list_for_instance(any()).thenReturn([available_backup,
                                                          failed_backup])
        when(BackupsController)._verify_swift_auth_token(any()).thenReturn(
            None)
        when(Backup).create(any(), backup.instance_id, backup.name,
                            backup.description).thenReturn(backup)
        when(api.API).create_backup(any()).thenReturn(None)
        result = self.controller.create(req, data, 'tenant 123')
        self.assertEqual(result.status, 202)
        result_backup = result._data['backup']
        self.assertEqual(result_backup['id'], backup.id)
        self.assertEqual(result_backup['name'], backup.name)
        self.assertEqual(result_backup['description'], backup.description)
        self.assertEqual(result_backup['locationRef'], backup.location)
        self.assertEqual(result_backup['instanceRef'], backup.instance_id)
        self.assertEqual(result_backup['created'], backup.created)
        self.assertEqual(result_backup['updated'], backup.updated)
        self.assertEqual(result_backup['status'], backup.state)

    def test_delete_backup_not_found(self):

        req = mock()
        req.environ = {wsgi.CONTEXT_KEY: 'Context'}
        when(Backup).get_by_id(any()).thenRaise(exception.NotFound)
        self.assertRaises(exception.NotFound, self.controller.delete, req,
                          'tenant 123', 'backup_id')

    def test_delete_backup_is_running(self):

        backup = mock()
        backup.state = BackupState.NEW

        req = mock()
        req.environ = {wsgi.CONTEXT_KEY: 'Context'}
        when(Backup).get_by_id(any()).thenReturn(backup)
        self.assertRaises(exception.BackupAlreadyRunning,
                          self.controller.delete, req,
                          'tenant 123', 'backup_id')
