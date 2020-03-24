# Copyright (c) 2020 OpenStack Foundation
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

from eventlet import event
from eventlet import greenthread

from neutron_lib import context
from neutron_lib.plugins import directory
from neutron_lib import worker

from networking_opencontrail import repository
from networking_opencontrail.sync.synchronizers import NetworkSynchronizer

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class TFSyncWorker(worker.BaseWorker):
    def __init__(self, device_types_to_omit):
        super(TFSyncWorker, self).__init__()
        self.device_types_to_omit = device_types_to_omit
        self.synchronizers = [
            NetworkSynchronizer(),
        ]
        self._thread = None
        self._running = False
        self.done = event.Event()

    def start(self, **kwargs):
        super(TFSyncWorker, self).start()
        LOG.info("ML2TFSynchronizer worker started")
        self._running = True
        self._thread = greenthread.spawn(self.sync_loop)

    def stop(self, graceful=True):
        if graceful:
            self._running = False
        else:
            self._thread.kill()

    def wait(self):
        return self.done.wait()

    def reset(self):
        self.stop()
        self.wait()
        self.start()

    def sync_loop(self):
        while self._running:
            try:
                repository.connect()
                self._synchronize()
            except repository.ConnectionError:
                LOG.error(
                    "Error while connecting to Contrail."
                    "Check APISERVER config section.")
            except Exception:
                LOG.exception("Periodic Sync Failed")

            greenthread.sleep(5)

        self.done.send()

    def _synchronize(self):
        for synchronizer in self.synchronizers:
            synchronizer.synchronize()

    @property
    def _core_plugin(self):
        return directory.get_plugin()

    @property
    def _context(self):
        return context.get_admin_context()
