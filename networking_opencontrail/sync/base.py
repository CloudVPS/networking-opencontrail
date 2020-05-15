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

from networking_opencontrail import repository

from neutron_lib import context
from neutron_lib.plugins import directory

from oslo_log import log as logging

import six

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class ResourceSynchronizer(object):
    """Abstract Synchronizer class.

    This class has properties that are used by all Synchronizers already
    implemented. It also enforces synchronize() method implementation in all
    children classes.
    """

    @abc.abstractmethod
    def synchronize(self):
        pass

    @property
    def _core_plugin(self):
        return directory.get_plugin()

    @property
    def _context(self):
        return context.get_admin_context()


@six.add_metaclass(abc.ABCMeta)
class OneToOneResourceSynchronizer(ResourceSynchronizer):
    """A base one-to-one Synchronizer class.

    It implements a concrete way of synchronizing resources, which is useful
    when TF and Neutron resources correspond to each other (i.e. have the same
    uuids). The synchronize() method calculates the diff between uuid lists
    in TF and Neutron and uses resource-specific methods implemented by the
    child classes to create/delete resources that are out-of-sync.
    """
    def __init__(self):
        self.to_create = []
        self.to_delete = []

    def synchronize(self):
        """Synchronize resources.

        Call calculate_diff to prepare lists of uuids to be used by
        resource-specific methods called after that.
        """
        self.calculate_diff()
        self._delete_resources()
        self._create_resources()

    def calculate_diff(self):
        """Calculate Neutron/TF resource diff.

        Use resource-specific methods implemented by child classes to get
        lists of given resources both from TF and Neutron. Compare the
        lists and populate to_create and to_delete lists with objects that are
        out of sync.
        """
        tf_resources = self._get_tf_resources()
        neutron_resources = self._get_neutron_resources()
        neutron_res_ids = set(
            [resource["id"] for resource in neutron_resources]
        )
        tf_res_ids = set([resource.get_uuid() for resource in tf_resources])

        res_ids_to_delete = tf_res_ids - neutron_res_ids
        res_ids_to_create = neutron_res_ids - tf_res_ids

        self.to_delete = [
            resource
            for resource in tf_resources
            if resource.get_uuid() in res_ids_to_delete
            and not self._ignore_tf_resource(resource)
        ]
        self.to_create = [
            resource
            for resource in neutron_resources
            if resource["id"] in res_ids_to_create
            and not self._ignore_neutron_resource(resource)
        ]

        self._log_diff(neutron_resources, tf_resources)

    def _create_resources(self):
        for resource in list(self.to_create):
            try:
                self._create_resource(resource)
                self.to_create.remove(resource)
            except Exception:
                LOG.exception(
                    "Create %s: %s Failed",
                    self.LOG_RES_NAME,
                    resource["id"]
                )

    def _delete_resources(self):
        for resource in list(self.to_delete):
            try:
                self._delete_resource(resource.get_uuid())
                self.to_delete.remove(resource)
            except Exception:
                LOG.exception(
                    "Delete %s: %s Failed",
                    self.LOG_RES_NAME,
                    resource.get_uuid()
                )

    def _log_diff(self, neutron_resources, tf_resources):
        if self.to_create or self.to_delete:
            LOG.info(
                "%ss in Neutron: %s",
                self.LOG_RES_NAME,
                len(neutron_resources)
            )
            LOG.info(
                "%ss in TF: %s",
                self.LOG_RES_NAME,
                len(tf_resources)
            )
        if self.to_delete:
            LOG.info(
                "%ss to delete in TF: %s",
                self.LOG_RES_NAME,
                self.to_delete
            )
        if self.to_create:
            LOG.info(
                "%ss to create in TF: %s",
                self.LOG_RES_NAME,
                self.to_create
            )

    def _ignore_neutron_resource(self, resource):
        """Tell if Neutron resource should be ignored.

        Child class should provide the implementation that allows certain
        Neutron resources to be ignored during sync.

        By default it returns False, so that no Neutron resource gets ignored.

        :param resource: Neutron resource
        :type: dict
        :return: True for each resource that needs to be ignored.
        :rtype: bool
        """
        return False

    def _ignore_tf_resource(self, resource):
        """Tell if TF resource should be ignored.

        Child class should provide the implementation that allows certain
        TF resources to be ignored during sync.

        By default it returns False, so that no TF resource gets ignored.

        :param resource: TF resource
        :return: True for each resource that needs to be ignored.
        :rtype: bool
        """
        return False

    @staticmethod
    def _no_ml2_tag(resource):
        return not repository.ml2_tag_manager.check(resource)

    @abc.abstractmethod
    def _get_tf_resources(self):
        """Get a list of TF resources.

        Child class should provide the implementation that returns a list
        of TF resources.

        :return: List of vnc_api objects
        :rtype: list
        """
        pass

    @abc.abstractmethod
    def _get_neutron_resources(self):
        """Get a list of Neutron resources.

        Child class should provide the implementation that returns a list
        of Neutron resources.

        :return: List of Neutron objects
        :rtype: list
        """
        pass

    @abc.abstractmethod
    def _create_resource(self, resource):
        """Create a resource in TF.

        Child class should provide the implementation that creates the
        resource in TF database.

        :param resource: Neutron resource to be created in TF
        :type: dict
        """
        pass

    @abc.abstractmethod
    def _delete_resource(self, resource_id):
        """Delete resource from TF.

        Child class should provide the implementation that deletes the
        resource from TF database.

        :param resource_id: Resource's UUID
        :type: str
        """
        pass
