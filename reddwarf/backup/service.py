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
from reddwarf.backup.models import Backup as model
from reddwarf.taskmanager import api as task_api
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
        backups = model.list(context)
        return wsgi.Result(views.BackupViews(backups).data(), 200)

    def create(self, req, body, tenant_id):

        context = req.environ[wsgi.CONTEXT_KEY]
        self._verify_swift_auth_token(context)
        data = body['backup']
        instance_id = data['instance']
        backup = model.create(context, instance_id,
                              data['name'], data['description'])
        task_api.API(context).create_backup(instance_id)
        return wsgi.Result(views.BackupView(backup).data(), 202)

    def delete(self, req, tenant_id, id):

        context = req.environ[wsgi.CONTEXT_KEY]
        self._verify_swift_auth_token(context)

        #TODO
        # Invoke taskmanager to delete the backup from swift

        model.delete(id)
        return wsgi.Result(None, 202)

    def _verify_swift_auth_token(self, context):
        try:
            client = create_swift_client(context)
            client.get_account()
        except ClientException:
            raise exception.SwiftAuthError(tenant_id=context.tenant)
