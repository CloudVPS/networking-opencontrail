# Copyright (c) 2016 OpenStack Foundation
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
from oslo_concurrency import lockutils
from oslo_log import log as logging

from neutron_lib.plugins.ml2 import api

from networking_opencontrail.common.constants import NTF_SYNC_LOCK_NAME
from networking_opencontrail.common import utils
from networking_opencontrail.drivers import drv_opencontrail as drv
from networking_opencontrail.ml2 import opencontrail_sg_callback
from networking_opencontrail import repository
from networking_opencontrail.sync import worker


LOG = logging.getLogger(__name__)


class OpenContrailMechDriver(api.MechanismDriver):
    """Main ML2 Mechanism driver from OpenContrail.

    This driver deals with all resources managed through ML2
    Plugin. Additionally, it manages the Security Groups
    Note: All the xxx_precommit() calls are ignored at the
    moment as there is no relevance for them in the OpenContrial
    SDN controller.
    """

    def initialize(self):
        utils.register_vnc_api_options()
        tf_driver = drv.OpenContrailDrivers()

        repository.initialize()

        try:
            repository.connect()
        except repository.ConnectionError:
            LOG.error(
                "Error while connecting to Contrail."
                "Check APISERVER config section.")

        self.drv = tf_driver
        self.sg_handler = (
            opencontrail_sg_callback.OpenContrailSecurityGroupHandler(self))

        LOG.info("Initialization of networking-opencontrail plugin: COMPLETE")

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def create_network_postcommit(self, context):
        """Create a network in OpenContrail."""
        q_network = context.current
        repository.network.create(q_network=q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def delete_network_postcommit(self, context):
        """Delete a network from OpenContrail."""
        q_network = context.current
        repository.network.delete(q_network=q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def update_network_postcommit(self, context):
        """Update an existing network in OpenContrail."""
        q_network = context.current
        old_q_network = context.original
        repository.network.update(old_q_network=old_q_network,
                                  q_network=q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def create_subnet_postcommit(self, context):
        """Create a subnet in OpenContrail."""
        subnet = context.current
        repository.subnet.create(subnet)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def delete_subnet_postcommit(self, context):
        """Delete a subnet from OpenContrail."""
        subnet = context.current
        repository.subnet.delete(subnet)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def update_subnet_postcommit(self, context):
        """Update a subnet in OpenContrail."""
        subnet = context.current
        repository.subnet.update(subnet)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def create_port_postcommit(self, context):
        """Create a port in OpenContrail."""
        q_port = context.current
        q_network = context.network.current

        repository.vpg.create(q_port, q_network)
        repository.vmi.create(q_port, q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def update_port_postcommit(self, context):
        """Update a port in OpenContrail."""
        q_port = context.current
        old_q_port = context.original
        q_network = context.network.current

        repository.vmi.delete(old_q_port, q_network, context._plugin_context)
        repository.vpg.delete(old_q_port, q_network)

        repository.vpg.create(q_port, q_network)
        repository.vmi.create(q_port, q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def delete_port_postcommit(self, context):
        """Delete a port from OpenContrail."""
        q_port = context.current
        q_network = context.network.current

        repository.vmi.delete(q_port, q_network, context._plugin_context)
        repository.vpg.delete(q_port, q_network)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def create_security_group(self, context, sg):
        """Create a Security Group in OpenContrail."""
        # vnc_openstack does not allow to create default security group
        if sg.get('name') == 'default':
            sg['name'] = 'default-openstack'
            sg['description'] = 'default-openstack security group'
        sec_g = {'security_group': sg}
        try:
            self.drv.create_security_group(context, sec_g)
        except Exception:
            LOG.exception('Failed to create Security Group %s' % sg)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def delete_security_group(self, context, sg):
        """Delete a Security Group from OpenContrail."""
        sg_id = sg.get('id')
        try:
            self.drv.delete_security_group(context, sg_id)
        except Exception:
            LOG.exception('Failed to delete Security Group %s' % sg_id)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def update_security_group(self, context, sg_id, sg):
        """Update a Security Group in OpenContrail."""
        sec_g = {'security_group': sg}
        try:
            self.drv.update_security_group(context, sg_id, sec_g)
        except Exception:
            LOG.exception('Failed to update Security Group %s' % sg_id)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def create_security_group_rule(self, context, sgr):
        """Create a Security Group Rule in OpenContrail."""
        sgr_r = {'security_group_rule': sgr}
        try:
            self.drv.create_security_group_rule(context, sgr_r)
        except Exception:
            LOG.exception('Failed to create Security Group rule %s' % sgr)

    @lockutils.synchronized(NTF_SYNC_LOCK_NAME, external=True)
    def delete_security_group_rule(self, context, sgr_id):
        """Delete a Security Group Rule from OpenContrail."""
        try:
            self.drv.delete_security_group_rule(context, sgr_id)
        except Exception:
            LOG.exception('Failed to delete Security Group rule %s' % sgr_id)

    def get_workers(self):
        return [
            worker.TFSyncWorker()
        ]
