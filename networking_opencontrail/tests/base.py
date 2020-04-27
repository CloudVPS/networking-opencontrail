# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import os
import uuid

from random import randint
from time import time as now

from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient.v3 import client as keystone
from neutronclient.v2_0 import client as neutron
from oslotest import base
from vnc_api import vnc_api


class TestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""


class IntegrationTestCase(base.BaseTestCase):
    """Base test case for all integration tests."""

    @classmethod
    def setUpClass(cls):
        super(IntegrationTestCase, cls).setUpClass()
        controller_ip = os.getenv('CONTROLLER_IP', 'localhost')
        default_auth_url = 'http://{}/identity/v3'.format(controller_ip)
        cls.auth_url = os.getenv('OS_AUTH_URL', default_auth_url)
        cls.keystone_user = os.getenv('KEYSTONE_USER', 'admin')
        cls.keystone_password = os.getenv('KEYSTONE_PASSWORD', 'admin')
        cls.keystone_project = os.getenv('KEYSTONE_PROJECT', 'admin')
        cls.keystone_project_domain_id = os.getenv(
            'KEYSTONE_PROJECT_DOMAIN_ID', 'default')
        cls.keystone_user_domain_id = os.getenv(
            'KEYSTONE_USER_DOMAIN_ID', 'default')
        cls.provider = os.getenv('PROVIDER', 'public')
        cls.contrail_ip = os.getenv('CONTRAIL_IP', 'localhost')
        cls.contrail_api = vnc_api.VncApi(
            api_server_host=cls.contrail_ip, api_server_port=8082)

    def setUp(self):
        super(IntegrationTestCase, self).setUp()

        auth = identity.V3Password(
            auth_url=self.auth_url,
            username=self.keystone_user,
            password=self.keystone_password,
            project_name=self.keystone_project,
            project_domain_id=self.keystone_project_domain_id,
            user_domain_id=self.keystone_user_domain_id)
        sess = session.Session(auth=auth)

        self.neutron = neutron.Client(session=sess)
        self.keystone = keystone.Client(session=sess)

        # Create keystone project and make TF synchronize it
        self.project = self._create_keystone_project_for_test()
        self.tf_project = self.tf_get('project', self.project.id)

        self.neutronCleanupQueue = []

    def tearDown(self):
        super(IntegrationTestCase, self).tearDown()
        for resource, f_delete in reversed(self.neutronCleanupQueue):
            f_delete(resource['id'])
        self.project.delete()
        self.tf_purge('project', self.project.id)

    def tf_create(self, resource):
        resource_type = resource.get_type()
        method_name = '{}_create'.format(resource_type.replace('-', '_'))
        create_method = getattr(self.contrail_api, method_name)

        return create_method(resource)

    def tf_get(self, resource_type, resource_id):
        resource_id = str(uuid.UUID(resource_id))
        method_name = '{}_read'.format(resource_type.replace('-', '_'))
        read_method = getattr(self.contrail_api, method_name)
        try:
            return read_method(id=resource_id)
        except vnc_api.NoIdError:
            return None

    def tf_list(self, resource_type, *args, **kwargs):
        method_name = '{}s_list'.format(resource_type.replace('-', '_'))
        list_method = getattr(self.contrail_api, method_name)
        resource_list = list_method(*args, **kwargs)
        if isinstance(resource_list, dict):
            resource_list = resource_list['{}s'.format(resource_type)]

        return resource_list

    def tf_update(self, resource):
        resource_type = resource.get_type()
        method_name = '{}_update'.format(resource_type.replace('-', '_'))
        update_method = getattr(self.contrail_api, method_name)

        return update_method(resource)

    def tf_delete(self, resource_type, resource_id):
        resource_id = str(uuid.UUID(resource_id))
        method_name = '{}_delete'.format(resource_type.replace('-', '_'))
        delete_method = getattr(self.contrail_api, method_name)

        if resource_type == 'virtual-port-group':
            vpg = self.tf_get(resource_type, resource_id)
            for vmi_ref in vpg.get_virtual_machine_interface_refs() or ():
                vmi = self.tf_get('virtual-machine-interface', vmi_ref["uuid"])
                vpg.del_virtual_machine_interface(vmi)
            self.contrail_api.virtual_port_group_update(vpg)

        try:
            delete_method(id=resource_id)
        except vnc_api.NoIdError:
            pass

    def tf_purge(self, resource_type, resource_id):
        try:
            self.tf_delete(resource_type, resource_id)
        except vnc_api.RefsExistError as exc:
            # exc.message doesn't always contain all children.
            # In these situations, we need to use tf_delete more times.
            hrefs = exc.message.split('\'')[1::2]
            for href in hrefs:
                child_resource_type = href.split('/')[-2]
                child_resource_id = href.split('/')[-1]
                self.tf_purge(child_resource_type, child_resource_id)

            try:
                self.tf_delete(resource_type, resource_id)
            except vnc_api.RefsExistError as exc:
                hrefs = exc.message.split('\'')[1::2]
                for href in hrefs:
                    child_resource_type = href.split('/')[-2]
                    child_resource_id = href.split('/')[-1]
                    self.tf_purge(child_resource_type, child_resource_id)

                self.tf_delete(resource_type, resource_id)

    def tf_delete_subnet(self, q_subnet):
        network = self.tf_get("virtual-network", q_subnet["network_id"])

        ipam_refs = network.get_network_ipam_refs()
        vn_subnets = ipam_refs[0]['attr']
        for subnet in list(vn_subnets.ipam_subnets):
            if subnet.subnet_uuid == q_subnet["id"]:
                vn_subnets.ipam_subnets.remove(subnet)

        network._pending_field_updates.add('network_ipam_refs')
        self.contrail_api.virtual_network_update(network)

    def _create_keystone_project_for_test(self):
        proj_name = self.__class__.__name__ + '-' + \
            str(int(now())) + '-' + \
            '{0:9}'.format(randint(100000000, 999999999))
        project = self.keystone.projects.create(
            name=proj_name, domain='default', description='', enabled=True)
        return project

    def _add_neutron_resource_to_cleanup(self, resource, f_cleanup):
        self.neutronCleanupQueue.append((resource, f_cleanup))

    def _remove_neutron_resource_from_cleanup(self, resource_tuple):
        self.neutronCleanupQueue.remove(resource_tuple)

    def q_create_resource(self, body):
        res_name = list(body)[0]
        f_create = getattr(self.neutron, 'create_' + res_name)
        f_delete = getattr(self.neutron, 'delete_' + res_name)

        resource = f_create(body)
        self._add_neutron_resource_to_cleanup(resource[res_name], f_delete)
        return resource

    def q_update_resource(self, resource, body):
        res_name = list(body)[0]
        f_update = getattr(self.neutron, 'update_' + res_name)
        updated_resource = f_update(resource['id'], body)
        return updated_resource

    def q_delete_resource(self, resource):
        match = [res for res in self.neutronCleanupQueue if resource in res]
        if match:
            match[0][1](match[0][0]['id'])
            self._remove_neutron_resource_from_cleanup(match[0])

    def q_create_network(self, name, **kwargs):
        network = {}
        network.update(kwargs)
        network['name'] = name
        network['project_id'] = self.project.id
        network_body = {}
        network_body['network'] = network
        return self.q_create_resource(network_body)

    def q_update_network(self, q_network, **kwargs):
        # kwargs contains dict with changed fields
        network_body = {'network': {}}
        network_body['network'].update(kwargs)
        return self.q_update_resource(q_network['network'], network_body)

    def q_create_subnet(self, name, network_id, ip_version, cidr, **kwargs):
        subnet = {}
        subnet.update(kwargs)
        subnet['name'] = name
        subnet['network_id'] = network_id
        subnet['ip_version'] = ip_version
        subnet['cidr'] = cidr
        subnet_body = {}
        subnet_body['subnet'] = subnet
        return self.q_create_resource(subnet_body)

    def q_update_subnet(self, subnet, **kwargs):
        subnet_body = {'subnet': {}}
        subnet_body['subnet'].update(kwargs)
        return self.q_update_resource(subnet['subnet'], subnet_body)

    def q_delete_network(self, network):
        self.q_delete_resource(network['network'])

    def q_delete_subnet(self, subnet):
        self.q_delete_resource(subnet['subnet'])

    def q_create_floating_ip(self, floating_network_id, **kwargs):
        floating_ip = {}
        floating_ip.update(kwargs)
        floating_ip['tenant_id'] = self.project.id
        floating_ip['project_id'] = self.project.id
        floating_ip['floating_network_id'] = floating_network_id
        floating_ip_body = {}
        floating_ip_body['floatingip'] = floating_ip
        return self.q_create_resource(floating_ip_body)

    def q_delete_floating_ip(self, floating_ip):
        self.q_delete_resource(floating_ip['floatingip'])

    def q_create_port(self, name, network_id, **kwargs):
        port = {}
        port.update(kwargs)
        port['name'] = name
        port['network_id'] = network_id
        port_body = {}
        port_body['port'] = port
        return self.q_create_resource(port_body)

    def q_delete_port(self, port):
        self.q_delete_resource(port['port'])

    def q_update_port(self, port, **kwargs):
        port_body = {'port': {}}
        port_body['port'].update(kwargs)
        return self.q_update_resource(port['port'], port_body)

    def q_create_security_group(self, name, **kwargs):
        security_group = {}
        security_group.update(kwargs)
        security_group['name'] = name
        security_group['project_id'] = self.project.id
        security_group_body = {}
        security_group_body['security_group'] = security_group
        return self.q_create_resource(security_group_body)

    def q_delete_security_group(self, security_group):
        self.q_delete_resource(security_group['security_group'])

    def q_update_security_group(self, security_group, **kwargs):
        security_group_body = {'security_group': {}}
        security_group_body['security_group'].update(kwargs)
        return self.q_update_resource(security_group['security_group'],
                                      security_group_body)

    def q_create_security_group_rule(self, security_group_id, **kwargs):
        security_group_rule = {}
        security_group_rule.update(kwargs)
        security_group_rule['security_group_id'] = security_group_id
        security_group_rule_body = {}
        security_group_rule_body['security_group_rule'] = security_group_rule
        return self.q_create_resource(security_group_rule_body)

    def q_delete_security_group_rule(self, rule):
        self.q_delete_resource(rule['security_group_rule'])


class FabricTestCase(IntegrationTestCase):
    """Base class for all Fabric related test cases.

    Provides helper methods for testing Fabric management functionality.
    """
    LAST_VLAN_ID = 100
    FABRIC = {'qfx-test-1': ['xe-0/0/0'],
              'qfx-test-2': ['xe-0/0/0',
                             'xe-1/1/1']}
    TOPOLOGY = {'compute-node': {'port-1':
                                 ('qfx-test-1', 'xe-0/0/0')},
                'compute-2': {'port-1':
                              ('qfx-test-2', 'xe-0/0/0'),
                              'port-2':
                              ('qfx-test-2', 'xe-1/1/1')}}

    @classmethod
    def setUpClass(cls):
        super(FabricTestCase, cls).setUpClass()
        cls._vnc_api = vnc_api.VncApi(api_server_host=cls.contrail_ip)
        cls._cleanup_topology_queue = []
        cls._cleanup_fabric_queue = []

        try:
            cls._make_fake_fabric()
            cls._make_fake_topology()
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        super(FabricTestCase, cls).tearDownClass()
        cls._cleanup()

    def setUp(self):
        super(FabricTestCase, self).setUp()

        self.test_network, self.vlan_id = self._make_vlan_network()

    def tearDown(self):
        self._cleanup_vpgs()
        super(FabricTestCase, self).tearDown()

    def _find_vmi(self, vmi_name):
        vmis = self.tf_list('virtual-machine-interface')
        return next((vmi['uuid'] for vmi in vmis
                     if vmi['fq_name'][-1] == vmi_name),
                    None)

    def _assert_vpg_deleted_or_not_ref(self, vpg_uuid, vmi_uuid):
        vpg = self.tf_get('virtual-port-group', vpg_uuid)
        if vpg:
            vpg = self.tf_get('virtual-port-group', vpg_uuid)
            self.assertFalse(self._check_vpg_contains_vmi_ref(
                vpg, vmi_uuid))

    def _assert_dm_vmi(self, vmi_uuid, net_uuid, vlan):
        """Assert that VMI with bindings for DM is created properly.

            1. VMI uuid exists
            2. VMI is connected only to given network
            3. VMI has right VLAN tag
            4. VMI has reference to one VPG and this VPG has reference to it
            5. VMI is tagged with label=__ML2__ tag
        """

        self.assertIsNotNone(vmi_uuid)
        vmi = self.tf_get('virtual-machine-interface', vmi_uuid)

        self.assertEqual(1, len(vmi.get_virtual_network_refs() or ()))
        self.assertEqual(net_uuid, vmi.get_virtual_network_refs()[0]['uuid'])

        vmi_properties = vmi.get_virtual_machine_interface_properties()
        self.assertIsNotNone(vmi_properties)
        self.assertEqual(vlan, vmi_properties.get_sub_interface_vlan_tag())

        self.assertEqual(1, len(vmi.get_virtual_port_group_back_refs() or ()))
        vpg_uuid = vmi.get_virtual_port_group_back_refs()[0]['uuid']
        vpg = self.tf_get('virtual-port-group', vpg_uuid)
        self.assertTrue(self._check_vpg_contains_vmi_ref(vpg, vmi_uuid))

        tag_names = [tag_ref["to"][-1] for tag_ref in vmi.get_tag_refs() or ()]
        self.assertIn("label=__ML2__", tag_names)

    def _check_vpg_contains_vmi_ref(self, vpg, vmi_uuid):
        vmi_refs = vpg.get_virtual_machine_interface_refs() or ()
        for ref in vmi_refs:
            if ref['uuid'] == vmi_uuid:
                return True
        return False

    def _make_vlan_network(self):
        vlan_id = self.LAST_VLAN_ID = self.LAST_VLAN_ID + 1
        net = {'name': 'test_vlan_{}_network'.format(vlan_id),
               'admin_state_up': True,
               'provider:network_type': 'vlan',
               'provider:physical_network': self.provider,
               'provider:segmentation_id': vlan_id}
        network = self.q_create_network(**net)
        return network, vlan_id

    @classmethod
    def _make_fake_fabric(cls):
        try:
            fabric = cls._vnc_api.fabric_read(
                ["default-global-system-config", "fabric01"]
            )
            cls._fabric_uuid = fabric.get_uuid()
        except vnc_api.NoIdError:
            fabric = vnc_api.Fabric('fabric01')
            cls._fabric_uuid = cls._vnc_api.fabric_create(fabric)
        cls._cleanup_fabric_queue.append(('fabric', cls._fabric_uuid))

        for pr_name in cls.FABRIC:
            try:
                pr = cls._vnc_api.physical_router_read(
                    ["default-global-system-config", pr_name]
                )
                pr.set_fabric(fabric)
                pr_uuid = pr.get_uuid()
                cls._vnc_api.physical_router_update(pr)
            except vnc_api.NoIdError:
                pr = vnc_api.PhysicalRouter(pr_name)
                pr.set_fabric(fabric)
                pr_uuid = cls._vnc_api.physical_router_create(pr)
            cls._cleanup_fabric_queue.append(('physical_router', pr_uuid))

            for pi_name in cls.FABRIC[pr_name]:
                try:
                    pi = cls._vnc_api.physical_interface_read([
                        "default-global-system-config", pr_name, pi_name])
                    pi_uuid = pi.get_uuid()
                except vnc_api.NoIdError:
                    pi = vnc_api.PhysicalInterface(name=pi_name, parent_obj=pr)
                    pi_uuid = cls._vnc_api.physical_interface_create(pi)
                cls._cleanup_fabric_queue.append(
                    ('physical_interface', pi_uuid))

    @classmethod
    def _make_fake_topology(cls):
        for node_name in cls.TOPOLOGY:
            try:
                node = cls._vnc_api.node_read(
                    ["default-global-system-config", node_name]
                )
                node_uuid = node.get_uuid()
            except vnc_api.NoIdError:
                node = vnc_api.Node(node_name, node_hostname=node_name)
                node_uuid = cls._vnc_api.node_create(node)
            cls._cleanup_topology_queue.append(('node', node_uuid))

            for port_name, port_pi in cls.TOPOLOGY[node_name].items():
                try:
                    node_port = cls._vnc_api.port_read(
                        ["default-global-system-config", node_name, port_name]
                    )
                    port_uuid = node_port.get_uuid()
                except vnc_api.NoIdError:
                    ll_obj = vnc_api.LocalLinkConnection(
                        switch_info=port_pi[0],
                        port_id=port_pi[1])
                    bm_info = vnc_api.BaremetalPortInfo(
                        address='00-00-00-00-00-00',
                        local_link_connection=ll_obj)
                    node_port = vnc_api.Port(port_name, node,
                                             bms_port_info=bm_info)
                    port_uuid = cls._vnc_api.port_create(node_port)
                cls._cleanup_topology_queue.append(('port', port_uuid))

    def _cleanup_vpgs(self):
        fabric = self._vnc_api.fabric_read(id=self._fabric_uuid)
        for vpg_ref in fabric.get_virtual_port_groups() or ():
            vpg_uuid = vpg_ref['uuid']
            vpg = self._vnc_api.virtual_port_group_read(id=vpg_uuid)
            for vmi_ref in vpg.get_virtual_machine_interface_refs() or ():
                vmi = self._vnc_api.virtual_machine_interface_read(
                    vmi_ref["to"]
                )
                vpg.del_virtual_machine_interface(vmi)
            self._vnc_api.virtual_port_group_update(vpg)
            self._vnc_api.virtual_port_group_delete(id=vpg.uuid)

    @classmethod
    def _cleanup(cls):
        reraise = False

        for queue in [cls._cleanup_fabric_queue, cls._cleanup_topology_queue]:
            for resource, res_uuid in reversed(queue):
                try:
                    del_func = getattr(cls._vnc_api,
                                       "{}_delete".format(resource))
                    del_func(id=res_uuid)
                except vnc_api.NoIdError:
                    pass
                except Exception:
                    reraise = True

        if reraise:
            raise
