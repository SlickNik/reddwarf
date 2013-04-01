# Copyright 2013 Rackspace Hosting

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from eventlet.green import subprocess
import hashlib
from reddwarf.common import cfg

CONF = cfg.CONF

# Read in multiples of 128 bytes, since this is the size of an md5 digest block
# this allows us to update that while streaming the file.
#http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
CHUNK_SIZE = CONF.backup_chunk_size
MAX_FILE_SIZE = CONF.backup_segment_max_size
BACKUP_CONTAINER = CONF.backup_swift_container


def size(num_bytes):
    """Human readable filesize"""
    mb = 1024.0 ** 2
    return round(num_bytes / mb, 1)


class BackupError(Exception):
    """Error running the Backup Command."""


class BackupRunner(object):
    """
    Call out to subprocess and wrap the stdout in order to segment the output.
    """

    # The actual system call to run the backup
    cmd = None
    # The backup format type
    backup_type = None

    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.container = BACKUP_CONTAINER
        # how much we have written
        self.content_length = 0
        self.segment_length = 0
        self.process = None
        self.pid = None
        self.writer = None
        self.file_number = 0
        self.written = -1
        self.end_of_file = False
        self.end_of_segment = False
        self.checksum = hashlib.md5()
        self.schecksum = hashlib.md5()
        self.command = self.cmd % kwargs

    def run(self):
        self.process = subprocess.Popen(self.command, shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.pid = self.process.pid

    def __enter__(self):
        """Start up the process"""
        self.run()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up everything."""
        if exc_type is None:
            # See if the process reported an error
            try:
                err = self.process.stderr.read()
                if err:
                    raise BackupError(err)
            except OSError:
                pass
        # Make sure to terminate the process
        try:
            self.process.terminate()
        except OSError:
            # Already stopped
            pass

    @property
    def segment(self):
        return '%s_%08d' % (self.filename, self.file_number)

    @property
    def manifest(self):
        """Subclasses may overwrite this to declare a format (.gz, .tar)"""
        return self.filename

    @property
    def prefix(self):
        return '%s/%s_' % (self.container, self.filename)

    def read(self, chunk_size):
        """Wrap self.process.stdout.read to allow for segmentation."""
        if self.end_of_segment:
            self.segment_length = 0
            self.schecksum = hashlib.md5()
            self.end_of_segment = False

        # Upload to a new file if we are starting or too large
        if self.segment_length > (MAX_FILE_SIZE - CHUNK_SIZE):
            self.file_number += 1
            self.end_of_segment = True
            return ''

        chunk = self.process.stdout.read(CHUNK_SIZE)
        if not chunk:
            self.end_of_file = True
            return ''

        self.checksum.update(chunk)
        self.schecksum.update(chunk)
        self.content_length += len(chunk)
        self.segment_length += len(chunk)
        return chunk
