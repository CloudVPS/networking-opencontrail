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
from neutron_lib.plugins import constants as plugin_constants
from neutron_lib.plugins import directory
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_opencontrail import repository

LOG = logging.getLogger(__name__)


def validate_flavor(provider_name, router, context):
    """Validates router's flavor.

    Normally, base.L3ServiceProvider.owns_router method can be called for that
    purpose, but in some cases it's impossible. The method requires router to
    exist in Neutron's DB, but that's not always the case (while handling
    BEFORE_CREATE event, for example).
    """
    flavor_id = router['flavor_id']
    if flavor_id is q_const.ATTR_NOT_SPECIFIED:
        return False

    flavor_plugin = directory.get_plugin(plugin_constants.FLAVORS)
    provider = flavor_plugin.get_flavor_next_provider(
        context, flavor_id)[0]
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
    def router_create(self, resource, event, trigger, **kwargs):
        """Creates Logical Router in TF Database."""
        router = kwargs['router']
        context = kwargs['context']
        if not validate_flavor(self.provider_name, router, context):
            LOG.debug('Skipping router not managed by TF (%s)', router['id'])
            return
        repository.router.create(router)

    @registry.receives(resources.ROUTER, [events.BEFORE_DELETE])
    @log_helpers.log_method_call
    def router_delete(self, resource, event, trigger, **kwargs):
        """Deletes Logical Router from TF Database."""
        router_id = kwargs['router_id']
        context = kwargs['context']
        if not self.owns_router(context, router_id):
            LOG.debug('Skipping router not managed by TF (%s)', router_id)
            return
        repository.router.delete(router_id)

    @registry.receives(resources.ROUTER, [events.ABORT_CREATE])
    @log_helpers.log_method_call
    def router_abort_create(self, resource, event, trigger, **kwargs):
        """Deletes LR from TF DB when creation is aborted."""
        router = kwargs['router']
        context = kwargs['context']
        if not validate_flavor(self.provider_name, router, context):
            LOG.debug('Skipping router not managed by TF (%s)', router['id'])
            return
        repository.router.delete(router['id'])
