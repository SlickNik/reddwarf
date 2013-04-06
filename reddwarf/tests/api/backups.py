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
from nose.tools import assert_equal, assert_false, assert_true, assert_raises
from proboscis import test
from reddwarf.tests.fakes.swift import SwiftClientStub
from reddwarfclient import exceptions
from reddwarf.tests.config import CONFIG
from reddwarf.tests.api.instances import WaitForGuestInstallationToFinish
from reddwarf.tests.api.instances import instance_info


GROUP = "dbaas.api.backups"
CREATE_BACKUP_GROUP = "dbaas.api.backups.create"
LIST_BACKUP_GROUP = "dbaas.api.backups.list"
DELETE_BACKUP_GROUP = "dbaas.api.backups.delete"
BACKUP_NAME = 'backup_test'
BACKUP_DESC = 'test description'


@test(depends_on_classes=[WaitForGuestInstallationToFinish],
      groups=[GROUP, CREATE_BACKUP_GROUP])
class CreateBackups(object):

    @test
    def test_backup_create_instance_not_found(self):
        """test create backup with unknown instance"""

        assert_raises(exceptions.NotFound, instance_info.dbaas.backups.create,
                      'backup_test', 'instance_id', 'test description')

    @test
    def test_backup_create_instance(self):
        """test create backup for a given instance"""

        if CONFIG.fake_mode:
            client_stub = SwiftClientStub()
            client_stub.with_account("tenant_id")

        result = instance_info.dbaas.backups.create(BACKUP_NAME,
                                                    instance_info.id,
                                                    BACKUP_DESC)

        assert_equal(BACKUP_NAME, result.name)
        assert_equal(BACKUP_DESC, result.description)
        assert_equal(instance_info.id, result.instanceRef)
        assert_equal('NEW', result.status)


@test(runs_after_groups=[CREATE_BACKUP_GROUP],
      groups=[GROUP, LIST_BACKUP_GROUP])
class ListBackups(object):

    @test
    def test_backup_create_another_backup_running(self):
        """test create backup when another backup is running"""
        assert_raises(exceptions.ClientException,
                      instance_info.dbaas.backups.create,
                      'backup_test2', instance_info.id, 'test description2')

    @test
    def test_backup_list(self):
        """test list backups"""

        result = instance_info.dbaas.backups.list()
        assert_equal(1, len(result))
        backup = result[0]
        assert_equal(BACKUP_NAME, backup.name)
        assert_equal(BACKUP_DESC, backup.description)
        assert_equal(instance_info.id, backup.instanceRef)
        assert_equal('NEW', backup.status)


@test(runs_after_groups=[LIST_BACKUP_GROUP],
      groups=[GROUP, DELETE_BACKUP_GROUP])
class DeleteBackups(object):

    @test
    def test_backup_delete_not_found(self):
        """test delete unknown backup"""
        assert_raises(exceptions.NotFound, instance_info.dbaas.backups.delete,
                      'backup_not_existent')

    @test
    def test_backup_delete_still_running(self):
        """test delete backup when it is running"""
        result = instance_info.dbaas.backups.list()
        backup = result[0]
        assert_raises(exceptions.ClientException,
                      instance_info.dbaas.backups.delete,
                      backup.id)
