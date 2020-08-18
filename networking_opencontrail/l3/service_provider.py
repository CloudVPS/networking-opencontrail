# Copyright (c) 2019 OpenStack Foundation
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

from neutron.services.l3_router.service_providers import base
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as q_const

from oslo_concurrency import lockutils
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_opencontrail.constants import NTF_SYNC_LOCK_NAME
from networking_opencontrail.neutron import neutron_client
from networking_opencontrail import repository

LOG = logging.getLogger(__name__)


def validate_flavor(provider_name, router, context):
    """Validates router's flavor.

    Normally, base.L3ServiceProvider.owns_router method can be called for that
    purpose, but in some cases it's impossible. The method requires router to
    exist in Neutron's DB, but that's not always the case (while handling
    BEFORE_CREATE event, for example).
    """
    flavor_id = router['flavor_id'] or q_const.ATTR_NOT_SPECIFIED
    if flavor_id is q_const.ATTR_NOT_SPECIFIED:
        return False

    provider = neutron_client.get_provider(context, flavor_id)

    return str(provider['driver']) == provider_name


@registry.has_registry_receivers
class TFL3ServiceProvider(base.L3ServiceProvider):
    """L3 Service Provider class for Tungsten Fabric

    Implements methods used to propagate information from L3 related Neutron
    events to TF.
    """
    @log_helpers.log_method_call
    def __init__(self, l3_plugin):
        super(TFL3ServiceProvider, self).__init__(l3_plugin)
        self.provider_name = __name__ + "." + self.__class__.__name__

    @registry.receives(resources.ROUTER, [events.BEFORE_CREATE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_create(self, resource, event, trigger, **kwargs):
        """Creates Logical Router in TF Database."""
        router = kwargs['router']
        context = kwargs['context']
        if not validate_flavor(self.provider_name, router, context):
            LOG.debug('Skipping router not managed by TF (%s)', router['id'])
            return
        repository.router.create(router)

    @registry.receives(resources.ROUTER, [events.ABORT_CREATE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_abort_create(self, resource, event, trigger, **kwargs):
        """Deletes LR from TF DB when creation is aborted."""
        router = kwargs['router']
        context = kwargs['context']
        if not validate_flavor(self.provider_name, router, context):
            LOG.debug('Skipping router not managed by TF (%s)', router['id'])
            return
        repository.router.delete(router['id'])

    @registry.receives(resources.ROUTER, [events.BEFORE_DELETE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_delete(self, resource, event, trigger, **kwargs):
        """Deletes Logical Router from TF Database."""
        router_id = kwargs['router_id']
        context = kwargs['context']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        repository.router.delete(router_id)

    @registry.receives(resources.ROUTER, [events.ABORT_DELETE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_abort_delete(self, resource, event, trigger, **kwargs):
        """Recreates LR in TF DB when deleting is aborted."""
        router_id = kwargs['router_id']
        context = kwargs['context']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        router = neutron_client.get_router(context, router_id)
        repository.router.create(router)

    @registry.receives(resources.ROUTER_INTERFACE, [events.BEFORE_CREATE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_add_interface(self, resource, event, trigger, **kwargs):
        """Creates VMI in TF for a LR interface and attaches it to LR."""
        context = kwargs['context']
        router_id = kwargs['router_db']['id']
        port = kwargs['port']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        repository.router.add_interface(router_id, port)

    @registry.receives(resources.ROUTER_INTERFACE, [events.ABORT_CREATE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_abort_add_interface(self, resource, event, trigger, **kwargs):
        """Deletes LR VMI from TF DB when adding interface is aborted."""
        context = kwargs['context']
        router_id = kwargs['router_db']['id']
        port_id = kwargs['port']['id']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        repository.router.remove_interface(router_id, port_id)

    @registry.receives(resources.PORT, [events.BEFORE_DELETE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_remove_interface(self, resource, event, trigger, **kwargs):
        """Deletes the LR VMI from TF.

        Router interface callback only provides router_id and subnet_id.
        Because of this, this callback reacts to port being deleted instead of
        router interface, since it's more convenient to find the VMI that needs
        to be deleted based on information this event provides.
        """
        context = kwargs['context']
        port_id = kwargs['port_id']
        port = neutron_client.get_port(context, port_id)
        if port['device_owner'] != 'network:router_interface':
            return
        router_id = port['device_id']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        repository.router.remove_interface(router_id, port_id)

    @registry.receives(resources.PORT, [events.ABORT_DELETE])
    @log_helpers.log_method_call
    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def router_abort_remove_interface(
            self, resource, event, trigger, **kwargs):
        """Recreates the LR VMI in TF when removing interface is aborted.

        Router interface callback only provides router_id and subnet_id.
        Because of this, this callback reacts to port being deleted instead of
        router interface, since it's more convenient to recreate the VMI based
        on information this event provides.
        """
        context = kwargs['context']
        port_id = kwargs['port_id']
        port = neutron_client.get_port(context, port_id)
        if port['device_owner'] != 'network:router_interface':
            return
        router_id = port['device_id']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        router = neutron_client.get_router(context, router_id)
        repository.router.add_interface(router, port)
