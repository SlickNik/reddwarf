# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
#

import abc
from reddwarf.guestagent.strategy import Strategy
from reddwarf.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class BackupStrategy(Strategy):
    """ Base class for Backup and Restore Strategy implementations """
    __strategy_type__ = 'backup'
    __strategy_ns__ = 'reddwarf.guestagent.strategies.backup'

    def __init__(self, central_service):
        super(BackupStrategy, self).__init__()

    @abc.abstractmethod
    def create_backup(self, context, backup_location, output_stream):
        """ Create a backup of the backup_location to the output_stream """

    @abc.abstractmethod
    def restore_backup(self, context, restore_location, input_stream):
        """ Restore a backup from the input stream to the restore_location """

    @abc.abstractmethod
    def check_backup_state(self, context, backup_cookie):
        """ Find the state of an in progress backup """

    @abc.abstractmethod
    def check_restore_state(self, context, restore_cookie):
        """ Find the state of an in progress restore """
