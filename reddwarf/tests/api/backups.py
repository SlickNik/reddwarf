# Copyright 2011 OpenStack LLC.
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
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_raises
from proboscis import test
from proboscis.decorators import time_out
from reddwarf.tests.util import poll_until
from reddwarfclient import exceptions
from reddwarf.tests.api.instances import WaitForGuestInstallationToFinish
from reddwarf.tests.api.instances import instance_info, assert_unprocessable


GROUP = "dbaas.api.backups"
BACKUP_NAME = 'backup_test'
BACKUP_DESC = 'test description'


@test(depends_on_classes=[WaitForGuestInstallationToFinish],
      groups=[GROUP])
class CreateBackups(object):

    @test
    def test_backup_create_instance_not_found(self):
        """test create backup with unknown instance"""
        assert_raises(exceptions.NotFound, instance_info.dbaas.backups.create,
                      'backup_test', 'instance_id', 'test description')

    @test
    def test_backup_create_instance(self):
        """test create backup for a given instance"""
        result = instance_info.dbaas.backups.create(BACKUP_NAME,
                                                    instance_info.id,
                                                    BACKUP_DESC)
        assert_equal(BACKUP_NAME, result.name)
        assert_equal(BACKUP_DESC, result.description)
        assert_equal(instance_info.id, result.instance_id)
        assert_equal('NEW', result.status)
        instance = instance_info.dbaas.instances.list()[0]
        assert_equal('BACKUP', instance.status)


@test(runs_after=[CreateBackups],
      groups=[GROUP])
class AfterBackupCreation(object):

    @test
    def test_instance_action_right_after_backup_create(self):
        """test any instance action while backup is running"""
        assert_unprocessable(instance_info.dbaas.instances.resize_volume,
                             instance_info.id, 1)

    @test
    def test_backup_create_another_backup_running(self):
        """test create backup when another backup is running"""
        assert_unprocessable(instance_info.dbaas.backups.create,
                             'backup_test2', instance_info.id,
                             'test description2')

    @test
    def test_backup_delete_still_running(self):
        """test delete backup when it is running"""
        result = instance_info.dbaas.backups.list()
        backup = result[0]
        assert_unprocessable(instance_info.dbaas.backups.delete, backup.id)

    @test
    def test_backup_create_quota_exceeded(self):
        """test quota exceeded when creating a backup"""
        instance_info.dbaas_admin.quota.update(instance_info.user.tenant_id,
                                               {'backups': 1})
        assert_raises(exceptions.OverLimit,
                      instance_info.dbaas.backups.create,
                      'Too_many_backups', instance_info.id, BACKUP_DESC)


@test(runs_after=[AfterBackupCreation],
      groups=[GROUP])
class WaitForBackupCreateToFinish(object):
    """
        Wait until the backup create is finished.
    """

    @test
    @time_out(60 * 30)
    def test_backup_created(self):
        # This version just checks the REST API status.
        def result_is_active():
            backup = instance_info.dbaas.backups.list()[0]
            if backup.status == "COMPLETED":
                return True
            else:
                assert_not_equal("FAILED", backup.status)
                return False

        poll_until(result_is_active)


@test(runs_after=[WaitForBackupCreateToFinish],
      groups=[GROUP])
class ListBackups(object):

    @test
    def test_backup_list(self):
        """test list backups"""
        result = instance_info.dbaas.backups.list()
        assert_equal(1, len(result))
        backup = result[0]
        assert_equal(BACKUP_NAME, backup.name)
        assert_equal(BACKUP_DESC, backup.description)
        assert_equal(instance_info.id, backup.instance_id)
        assert_equal('COMPLETED', backup.status)

    @test
    def test_backup_list_for_instance(self):
        """test list backups"""
        result = instance_info.dbaas.instances.backups(instance_info.id)
        assert_equal(1, len(result))
        backup = result[0]
        assert_equal(BACKUP_NAME, backup.name)
        assert_equal(BACKUP_DESC, backup.description)
        assert_equal(instance_info.id, backup.instance_id)
        assert_equal('COMPLETED', backup.status)


@test(runs_after=[ListBackups],
      groups=[GROUP])
class DeleteBackups(object):

    @test
    def test_backup_delete_not_found(self):
        """test delete unknown backup"""
        assert_raises(exceptions.NotFound, instance_info.dbaas.backups.delete,
                      'backup_not_existent')
