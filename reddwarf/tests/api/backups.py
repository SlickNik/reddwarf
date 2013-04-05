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

from proboscis import before_class
from proboscis import test
from reddwarf.tests.fakes.swift import SwiftClientStub
from reddwarfclient import exceptions
from reddwarf.tests.config import CONFIG
from reddwarf.tests.util import create_dbaas_client
from reddwarf.tests.util.users import Requirements
from reddwarf.tests.api.instances import WaitForGuestInstallationToFinish
from reddwarf.tests.api.instances import instance_info


GROUP = "dbaas.api.backups"


@test(depends_on_classes=[WaitForGuestInstallationToFinish],
      groups=[GROUP])
class CreateBackups(object):

    @before_class
    def setUp(self):
        reqs = Requirements(is_admin=False)
        user = CONFIG.users.find_user(reqs)
        self.rd_client = create_dbaas_client(user)

    @test
    def test_backup_create_instance_not_found(self):
        """test create backup with unknown instance"""

        assert_raises(exceptions.NotFound, self.rd_client.backups.create,
                      'backup_test', 'instance_id', 'test description')

    @test
    def test_backup_create_instance(self):
        """test create backup for a given instance"""

        if CONFIG.fake_mode:
            client_stub = SwiftClientStub()
            client_stub.with_account('tenant_id')

        result = self.rd_client.backups.create('backup_test',
                                               instance_info.id,
                                               'test description')

        assert_equal('backup_test', result.name)
        assert_equal('test description', result.description)
        assert_equal(instance_info.id, result.instanceRef)
        assert_equal('NEW', result.status)

        # Check backup create when another one is running
        assert_raises(exceptions.ClientException,
                      self.rd_client.backups.create,
                      'backup_test2', instance_info.id, 'test description')
