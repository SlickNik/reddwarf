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
from reddwarf.guestagent.strategy import Strategy
from reddwarf.common import cfg

from eventlet.green import subprocess

CONF = cfg.CONF
CHUNK_SIZE = CONF.backup_chunk_size


class RestoreError(Exception):
    """Error running the Backup Command."""


class RestoreRunner(Strategy):
    """ Base class for Restore Strategy implementations """
    """Restore a database from a previous backup."""

    __strategy_type__ = 'restore_runner'
    __strategy_ns__ = 'reddwarf.guestagent.strategies.restore'

    # The actual system calls to run the restore and prepare
    restore_cmd = None
    prepare_cmd = None

    # The backup format type
    restore_type = None

    def __init__(self, restore_stream, **kwargs):
        self.restore_stream = restore_stream
        self.restore_cmd = self.restore_cmd % kwargs
        super(RestoreRunner, self).__init__()

    def execute_restore(self):
        self._run_restore()

    def __enter__(self):
        """Start up the process"""
        self._run_restore()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up everything."""
        if exc_type is None:
            # See if the process reported an error
            try:
                err = self.process.stderr.read()
                if err:
                    raise RestoreError(err)
            except OSError:
                pass
        # Make sure to terminate the process
        try:
            self.process.terminate()
        except OSError:
            # Already stopped
            pass

    def _run_restore(self):
        with self.restore_stream as stream:
            self.process = subprocess.Popen(self.restore_cmd, shell=True,
                                            stdin=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            self.pid = self.process.pid
            content_length = 0
            chunk = stream.read(CHUNK_SIZE)
            while chunk:
                self.process.stdin.write(chunk)
                content_length += len(chunk)
                chunk = stream.read(CHUNK_SIZE)
