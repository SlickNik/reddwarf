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

from reddwarf.guestagent.strategies.restore import base
from reddwarf.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class MySQLDump(base.RestoreRunner):
    """ Implementation of Restore Strategy for MySQLDump """
    __strategy_name__ = 'mysqldump'
    is_zipped = True
    restore_cmd = 'mysql '\
                  '--password=%(password)s '\
                  '-u %(user)s'


class InnoBackupEx(base.RestoreRunner):
    """ Implementation of Restore Strategy for InnoBackupEx """
    __strategy_name__ = 'innobackupex'
    is_zipped = True
    restore_cmd = 'sudo xbstream -x %(restore_location)s'
    prepare_cmd = 'sudo innobackupex --apply-log %(restore_location)s '\
                  '2>/tmp/innoprepare.log'
