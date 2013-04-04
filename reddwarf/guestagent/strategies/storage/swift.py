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

from reddwarf.guestagent.strategies.storage import base
from reddwarf.openstack.common import log as logging
from reddwarf.common.remote import create_swift_client


LOG = logging.getLogger(__name__)


class SwiftStorage(base.Storage):
    """ Implementation of Storage Strategy for Swift """
    __strategy_name__ = 'swift'

    def __init__(self, context):
        super(SwiftStorage, self).__init__()
        self.connection = create_swift_client(context)

    def set_container(self, ):
        """ Set the container to store to.  """
        """ This creates the container if it doesn't exist.  """

    def save(self, save_location, stream):
        """ Persist information from the stream """

        # Create the container (save_location) if it doesn't already exist
        self.container_name = save_location
        self.connection.put_container(self.container_name)

        # Read from the stream and write to the container in swift
        while not stream.end_of_file:
            segment = stream.segment
            etag = self.connection.put_object(self.container_name,
                                              segment,
                                              stream)

            # Check each segment MD5 hash against swift etag
            # Raise an error and mark backup as failed
            if etag != stream.schecksum.hexdigest():
                print etag, stream.schecksum.hexdigest()
                return (False, "Error saving data to Swift!", None, None)

            checksum = stream.checksum.hexdigest()
            url = self.connection.url
            location = "%s/%s/%s" % (url, self.container_name, stream.manifest)

            # Create the manifest file
            headers = {'X-Object-Manifest': stream.prefix}
            self.connection.put_object(self.container_name,
                                       stream.manifest,
                                       contents='',
                                       headers=headers)

            return (True, "Successfully saved data to Swift!",
                    checksum, location)

    def load(self, context):
        """ Restore a backup from the input stream to the restore_location """
