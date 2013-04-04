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


class Storage(Strategy):
    """ Base class for Storage Strategy implementation """
    __strategy_type__ = 'storage'
    __strategy_ns__ = 'reddwarf.guestagent.strategies.storage'

    def __init__(self):
        super(Storage, self).__init__()

    @abc.abstractmethod
    def save(self, save_location, stream):
        """ Persist information from the stream """

    @abc.abstractmethod
    def load(self, context):
        """ Restore a backup from the input stream to the restore_location """
