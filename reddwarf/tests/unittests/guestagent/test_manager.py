#    Copyright 2012 OpenStack LLC
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
#    under the License

import os

from mockito import verify, when, unstub, any, mock, never
import testtools
from testtools.matchers import Is, Equals, Not
from reddwarf.common.context import ReddwarfContext

from reddwarf.guestagent.manager import Manager
from reddwarf.guestagent import dbaas, backup
from reddwarf.guestagent.volume import VolumeDevice


class GuestAgentManagerTest(testtools.TestCase):

    def setUp(self):
        super(GuestAgentManagerTest, self).setUp()
        self.context = ReddwarfContext()
        self.manager = Manager()

    def tearDown(self):
        super(GuestAgentManagerTest, self).tearDown()
        unstub()

    def test_update_status(self):
        mock_status = mock()
        when(dbaas.MySqlAppStatus).get().thenReturn(mock_status)
        self.manager.update_status(self.context)
        verify(dbaas.MySqlAppStatus).get()
        verify(mock_status).update()

    def test_create_database(self):
        when(dbaas.MySqlAdmin).create_database(['db1']).thenReturn(None)
        self.manager.create_database(['db1'])
        verify(dbaas.MySqlAdmin).create_database(['db1'])

    def test_create_database_empty(self):
        when(dbaas.MySqlAdmin).create_database(any()).thenReturn(None)
        self.manager.create_database([])
        verify(dbaas.MySqlAdmin, never).create_database(any())

    def test_create_database_none(self):
        when(dbaas.MySqlAdmin).create_database(any()).thenReturn(None)
        self.manager.create_database(None)
        verify(dbaas.MySqlAdmin, never).create_database(any())

    def test_create_user(self):
        when(dbaas.MySqlAdmin).create_user(['user1']).thenReturn(None)
        self.manager.create_user(['user1'])
        verify(dbaas.MySqlAdmin).create_user(['user1'])

    def test_create_user_empty(self):
        when(dbaas.MySqlAdmin).create_user(any()).thenReturn(None)
        self.manager.create_user([])
        verify(dbaas.MySqlAdmin, never).create_user(any())

    def test_create_user_none(self):
        when(dbaas.MySqlAdmin).create_user(any()).thenReturn(None)
        self.manager.create_user(None)
        verify(dbaas.MySqlAdmin, never).create_user(any())

    def test_delete_database(self):
        databases = ['db1']
        when(dbaas.MySqlAdmin).delete_database(databases).thenReturn(None)
        self.manager.delete_database(self.context, databases)
        verify(dbaas.MySqlAdmin).delete_database(databases)

    def test_delete_user(self):
        user = ['user1']
        when(dbaas.MySqlAdmin).delete_user(user).thenReturn(None)
        self.manager.delete_user(self.context, user)
        verify(dbaas.MySqlAdmin).delete_user(user)

    def test_list_databases(self):
        when(dbaas.MySqlAdmin).list_databases(None, None,
                                              False).thenReturn(['database1'])
        databases = self.manager.list_databases(self.context)
        self.assertThat(databases, Not(Is(None)))
        self.assertThat(databases, Equals(['database1']))
        verify(dbaas.MySqlAdmin).list_databases(None, None, False)

    def test_list_users(self):
        when(dbaas.MySqlAdmin).list_users(None, None,
                                          False).thenReturn(['user1'])
        users = self.manager.list_users(self.context)
        self.assertThat(users, Equals(['user1']))
        verify(dbaas.MySqlAdmin).list_users(None, None, False)

    def test_enable_root(self):
        when(dbaas.MySqlAdmin).enable_root().thenReturn('user_id_stuff')
        user_id = self.manager.enable_root(self.context)
        self.assertThat(user_id, Is('user_id_stuff'))
        verify(dbaas.MySqlAdmin).enable_root()

    def test_is_root_enabled(self):
        when(dbaas.MySqlAdmin).is_root_enabled().thenReturn(True)
        is_enabled = self.manager.is_root_enabled(self.context)
        self.assertThat(is_enabled, Is(True))
        verify(dbaas.MySqlAdmin).is_root_enabled()

    def test_create_backup(self):
        when(backup).backup(self.context, 'backup_id_123').thenReturn(None)
        # entry point
        Manager().create_backup(self.context, 'backup_id_123')
        # assertions
        verify(backup).backup(self.context, 'backup_id_123')

    def test_prepare_device_path_true(self):
        self._prepare_dynamic()

    def test_prepare_device_path_false(self):
        self._prepare_dynamic(device_path=None)

    def test_prepare_mysql_not_installed(self):
        self._prepare_dynamic(is_mysql_installed=False)

    def test_prepare_mysql_from_backup(self):
        self._prepare_dynamic(backup_id='backup_id_123abc')

    def test_prepare_mysql_from_backup(self):
        self._prepare_dynamic(backup_id='backup_id_123abc')

    def test_prepare_mysql_from_backup_with_root(self):
        self._prepare_dynamic(backup_id='backup_id_123abc',
                              is_root_enabled=True)

    def _prepare_dynamic(self, device_path='/dev/vdb', is_mysql_installed=True,
                         backup_id=None, is_root_enabled=False):

        if device_path:
            COUNT = 1
        else:
            COUNT = 0

        if is_mysql_installed:
            SEC_COUNT = 1
        else:
            SEC_COUNT = 0

        # TODO (juice) this should stub an instance of the MySqlAppStatus
        mock_status = mock()
        when(dbaas.MySqlAppStatus).get().thenReturn(mock_status)
        when(mock_status).begin_mysql_install().thenReturn(None)
        when(VolumeDevice).format().thenReturn(None)
        when(VolumeDevice).migrate_data(any()).thenReturn(None)
        when(VolumeDevice).mount().thenReturn(None)
        when(dbaas.MySqlApp).stop_mysql().thenReturn(None)
        when(dbaas.MySqlApp).start_mysql().thenReturn(None)
        when(dbaas.MySqlApp).install_if_needed().thenReturn(None)
        when(backup).restore(self.context, backup_id).thenReturn(None)
        when(dbaas.MySqlApp).secure().thenReturn(None)
        when(dbaas.MySqlApp).is_installed().thenReturn(is_mysql_installed)
        when(dbaas.MySqlAdmin).is_root_enabled().thenReturn(is_root_enabled)
        when(dbaas.MySqlAdmin).create_user().thenReturn(None)
        when(dbaas.MySqlAdmin).create_database().thenReturn(None)
        when(dbaas.MySqlAdmin).report_root_enabled(self.context).thenReturn(
            None)

        when(os.path).exists(any()).thenReturn(is_mysql_installed)
        # invocation
        self.manager.prepare(context=self.context, databases=None,
                             memory_mb='2048', users=None,
                             device_path=device_path,
                             mount_point='/var/lib/mysql',
                             backup_id=backup_id)
        # verification/assertion
        verify(mock_status).begin_mysql_install()

        verify(VolumeDevice, times=COUNT).format()
        verify(dbaas.MySqlApp, times=(COUNT * SEC_COUNT)).stop_mysql()
        verify(VolumeDevice, times=(COUNT * SEC_COUNT)).migrate_data(any())
        verify(dbaas.MySqlApp, times=(COUNT * SEC_COUNT)).start_mysql()
        if backup_id:
            verify(backup).restore(self.context, backup_id, '/var/lib/mysql')
        verify(dbaas.MySqlApp).install_if_needed()
        verify(dbaas.MySqlApp).secure('2048', keep_root=is_root_enabled)
        verify(dbaas.MySqlAdmin, never).create_database()
        verify(dbaas.MySqlAdmin, never).create_user()
        times_report = 1 if is_root_enabled else 0
        verify(dbaas.MySqlAdmin, times=times_report).report_root_enabled(
            self.context)

    def test_restart(self):
        mock_status = mock()
        when(dbaas.MySqlAppStatus).get().thenReturn(mock_status)
        mock_app = mock(dbaas.MySqlApp)
        when(dbaas).MySqlApp(mock_status).thenReturn(mock_app)
        when(mock_app).restart().thenReturn(None)
        self.manager.restart(self.context)
        verify(mock_app).restart()

    def test_start_mysql_with_conf_changes(self):
        updated_mem_size = '2048'
        mock_status = mock()
        when(dbaas.MySqlAppStatus).get().thenReturn(mock_status)
        mock_app = mock(dbaas.MySqlApp)
        when(dbaas).MySqlApp(mock_status).thenReturn(mock_app)
        when(mock_app).start_mysql_with_conf_changes(
            updated_mem_size).thenReturn(None)
        # invocation
        self.manager.start_mysql_with_conf_changes(self.context,
                                                   updated_mem_size)
        # verification
        verify(mock_app).start_mysql_with_conf_changes(updated_mem_size)

    def test_stop_mysql(self):
        mock_status = mock()
        when(dbaas.MySqlAppStatus).get().thenReturn(mock_status)
        mock_app = mock(dbaas.MySqlApp)
        when(dbaas).MySqlApp(mock_status).thenReturn(mock_app)
        when(mock_app).stop_mysql(
            do_not_start_on_reboot=False).thenReturn(None)
        # invocation
        self.manager.stop_mysql(self.context)
        # verification
        verify(mock_app).stop_mysql(do_not_start_on_reboot=False)
