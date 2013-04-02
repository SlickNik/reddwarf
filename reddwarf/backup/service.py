# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack LLC
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from reddwarf.common import wsgi
from reddwarf.common import exception
from reddwarf.common.remote import create_swift_client
from reddwarf.backup import views
from reddwarf.backup.models import BackupState
from reddwarf.backup.models import Backup
from reddwarf.instance import models
from reddwarf.taskmanager import api
from swiftclient.client import ClientException


class BackupsController(wsgi.Controller):
    """
    Controller for accessing backups in the OpenStack API.
    """

    def index(self, req, tenant_id):
        """
        Return all backups information for a tenant ID.
        """
        context = req.environ[wsgi.CONTEXT_KEY]
        backups = Backup.list(context)
        return wsgi.Result(views.BackupViews(backups).data(), 200)

    def create(self, req, body, tenant_id):

        context = req.environ[wsgi.CONTEXT_KEY]
        data = body['backup']
        instance_id = data['instance']

        # verify that the instance exist
        models.get_db_info(context, instance_id)

        # verify that no other backup for this instance is running
        running_backups = [b
                           for b in Backup.list_for_instance(instance_id)
                           if b.state != BackupState.COMPLETED
                           and b.state != BackupState.FAILED]
        if len(running_backups) > 0:
            raise exception.BackupAlreadyRunning(action='create',
                                                 backup_id=running_backups[
                                                     0].id)

        self._verify_swift_auth_token(context)

        backup = Backup.create(context, instance_id,
                               data['name'], data['description'])
        api.API(context).create_backup(instance_id)
        return wsgi.Result(views.BackupView(backup).data(), 202)

    def delete(self, req, tenant_id, id):

        context = req.environ[wsgi.CONTEXT_KEY]

        # verify that this backup is not running
        backup = Backup.get_by_id(id)
        if backup.state != BackupState.COMPLETED and backup.state != \
                BackupState.FAILED:
            raise exception.BackupAlreadyRunning(action='delete',
                                                 backup_id=id)

        self._verify_swift_auth_token(context)

        #TODO
        # Invoke taskmanager to delete the backup from swift

        Backup.delete(id)
        return wsgi.Result(None, 202)

    def _verify_swift_auth_token(self, context):
        try:
            client = create_swift_client(context)
            client.get_account()
        except ClientException:
            raise exception.SwiftAuthError(tenant_id=context.tenant)
