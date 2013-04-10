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
from reddwarf.common import cfg, utils

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
        self.prepare_cmd = self.prepare_cmd % kwargs \
            if hasattr(self, 'prepare_cmd') else None
        super(RestoreRunner, self).__init__()

    def __enter__(self):
        """Return the runner"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up everything."""
        if exc_type is None:
            utils.raise_if_process_errored(self.process, RestoreError)
            if hasattr(self, 'prep_process'):
                utils.raise_if_process_errored(self.prep_process, RestoreError)

        # Make sure to terminate the processes
        try:
            self.process.terminate()
            if hasattr(self, 'prep_process'):
                self.prep_process.terminate()
        except OSError:
            # Already stopped
            pass

    def restore(self):
        return self._run_restore()

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

        if self.prepare_cmd:
            self._run_prepare()

        return content_length

    def _run_prepare(self):
        self.prep_process = subprocess.Popen(self.prepare_cmd, shell=True,
                                             stdin=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        self.prep_pid = self.prep_process.pid
        self.prep_process.wait()
