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
import abc

from eventlet import event
from eventlet import greenthread

from neutron_lib import context
from neutron_lib.plugins import directory
from neutron_lib import worker

from oslo_log import log as logging

import six

LOG = logging.getLogger(__name__)


class TFSynchronizer(worker.BaseWorker):
    def __init__(self, tf_driver, device_types_to_omit):
        super(TFSynchronizer, self).__init__()
        self.driver = tf_driver
        self.device_types_to_omit = device_types_to_omit
        self.synchronizers = [
            NetworkSynchronizer(tf_driver),
        ]
        self._thread = None
        self._running = False
        self.done = event.Event()

    def start(self, **kwargs):
        super(TFSynchronizer, self).start()
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
                self._synchronize()
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


@six.add_metaclass(abc.ABCMeta)
class ResourceSynchronizer(object):
    def __init__(self, tf_driver):
        self.driver = tf_driver
        self.to_create = []
        self.to_delete = []

    def synchronize(self):
        self.calculate_diff()
        self._delete_resources()
        self._create_resources()

    def calculate_diff(self):
        tf_resources = self._get_tf_resources()
        neutron_resources = self._get_neutron_resources()
        neutron_res_ids = set(
            [resource["id"] for resource in neutron_resources]
        )
        tf_res_ids = set([resource["id"] for resource in tf_resources])

        res_ids_to_delete = tf_res_ids - neutron_res_ids
        res_ids_to_create = neutron_res_ids - tf_res_ids

        self.to_delete = [
            resource
            for resource in tf_resources
            if resource["id"] in res_ids_to_delete
            and not self._ignore_tf_resource(resource)
        ]
        self.to_create = [
            resource
            for resource in neutron_resources
            if resource["id"] in res_ids_to_create
            and not self._ignore_neutron_resource(resource)
        ]

        if self.to_create or self.to_delete:
            LOG.info(
                "%ss in Neutron: %s", self.LOG_RES_NAME, len(neutron_resources)
            )
            LOG.info("%ss in TF: %s", self.LOG_RES_NAME, len(tf_resources))
        if self.to_delete:
            LOG.info(
                "%ss to delete in TF: %s", self.LOG_RES_NAME, self.to_delete
            )
        if self.to_create:
            LOG.info(
                "%ss to create in TF: %s", self.LOG_RES_NAME, self.to_create
            )

    def _create_resources(self):
        for resource in list(self.to_create):
            try:
                self._create_resource(resource)
                self.to_create.remove(resource)
            except Exception:
                LOG.exception(
                    "Create %s: %s Failed", self.LOG_RES_NAME, resource["id"]
                )

    def _delete_resources(self):
        for resource in list(self.to_delete):
            try:
                self._delete_resource(resource["id"])
                self.to_delete.remove(resource)
            except Exception:
                LOG.exception(
                    "Delete %s: %s Failed", self.LOG_RES_NAME, resource["id"]
                )

    @abc.abstractmethod
    def _get_tf_resources(self):
        pass

    @abc.abstractmethod
    def _get_neutron_resources(self):
        pass

    @abc.abstractmethod
    def _create_resource(self, resource):
        pass

    @abc.abstractmethod
    def _delete_resource(self, resource_id):
        pass

    @abc.abstractmethod
    def _ignore_neutron_resource(self, resource):
        pass

    @abc.abstractmethod
    def _ignore_tf_resource(self, resource):
        pass

    @property
    def _core_plugin(self):
        return directory.get_plugin()

    @property
    def _context(self):
        return context.get_admin_context()


class NetworkSynchronizer(ResourceSynchronizer):
    LOG_RES_NAME = "Network"

    def _get_tf_resources(self):
        return self.driver.get_networks(self._context, filters={})

    def _get_neutron_resources(self):
        return self._core_plugin.get_networks(self._context)

    def _create_resource(self, resource):
        network = {"network": resource}
        self.driver.create_network(self._context, network)

    def _delete_resource(self, resource_id):
        self.driver.delete_network(self._context, resource_id)

    def _ignore_tf_resource(self, resource):
        return resource["fq_name"][1] == "default-project"

    def _ignore_neutron_resource(self, resource):
        return "_snat_" in resource["name"]
