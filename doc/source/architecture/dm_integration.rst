==================================
Device Manager integration details
==================================

Plugin can trigger Device Manager to automatically manage underlay: VLAN tags on
switch interfaces and VXLAN. Using this, compute hosts can be dynamically
connected to VLANs used by virtual machines that run on them.

Networking-opencontrail triggers DM by creating a *virtual-machine-interface* (VMI)
in Tungsten Fabric for each affected VM, that contains references
to the bindings for physical interfaces that need to be configured.
A single VMI is created on every for each network that has at least on VM connected it.
Any other actions, like pushing configuration, is done
by Tungsten Fabric/Device Manager.

Prerequisites in TF
===================

Plugin expects that at least fabric is onboarded. That means, switches and
their interfaces that will be used during integration are represented in TF API
as ``physical router`` and ``physical interfaces`` and physical router has
reference to the ``fabric`` object.

When topology is provided from TF API, it is also expected that any managed
compute hosts and all of its ports are represented by the ``node`` and ``port`` objects.
It is important that each node needs to have the same name as used by Open Stack and
any port that is connected to switch needs to have reference to the corresponding physical
interface object. Ports without PI refs will be ignored.

.. seealso::

    How to configure plugin for DM integration is described on page
    :doc:`../device_manager`. Onboarding fabric is out-of-scope of this
    document.


VPG and VMI
===========

VMI is per tuple (network, node) and contains:
    * name created from template ``vmi#<network_uuid>#<node_name>``
    * ``virtual_port_group_back_refs`` list that contains VPG of the node
    * ``virtual_network_refs`` list that contains the network
    * ``sub_interface_vlan_tag`` property with VLAN tag value
    * ``profile bindings`` dictionary that contains list of affected switches,
      their interfaces, fabric name and VPG name (if VPG object exists)

VPG is per node (openstack compute) and contains:
    * name created from template ``vpg#<node_name>``,
    * ``physical_interface_refs`` list that contains all physical interfaces to which the node is connected
    * ``virtual_machine_interface_refs`` list that contains all VMIs of the node

.. note::
    VPG is a ``virtual port group`` object in TF that groups physical
    interfaces. This provide support for both LAG and multihoming. More about
    them you can read in `Juniper VPG documentation <vpg_doc_>`_.

    .. _vpg_doc: https://www.juniper.net/documentation/en_US/contrail5.1/topics/concept/contrail-virtual-port-groups.html


Integration flow
================

Plugin calls methods for managing VPGs and VMIs during ``create_port_postcommit``,
``update_port_postcommit`` and ``delete_port_postcommit`` actions in ML2 framework.

On ``create_port_postcommit``:
    #. Check if the port needs VPG. If the answer is yes, then create VPG if not exists yet.
    #. Check if the port needs VMI. If the answer is yes, then create VMI if not exists yet.

On ``delete_port_postcommit``:
    #. Check if the any other ports needs VMI used by the removed port. If the answer is no, then delete this VMI.
    #. Check if the any other ports needs VPG used by the removed port. If the answer is no, then delete this VPG.

On ``update_port_postcommit``:
    #. Exec the 'delete_port_postcommit' logic for the old port.
    #. Exec the 'create_port_postcommit' logic for the new port.

Note: If port update does not impact the VMI/VPG state (network/host did not change), it will be ignored.

Port need VMI and VPG if:
    * port owner is compute (field 'device_owner' has a prefix 'compute:')
    * port has binding (field 'binding:host_id' exists)
    * port has network (field 'network_id' exists)
    * port network has VLAN ID (q_network has field 'provider:segmentation_id')

Expected result
===============

After ensuring the existence of the appropriate VMIs and VPGs, the plugin has
no more work left to do. After a while it is expected that related switches
will be configured to have VLAN tagging on specific ports and VXLAN. Each VLAN
tag is selected by plugin (from Open Stack VLAN virtual network), whereas VXLAN
id is managed by Tungsten Fabric (typically this is value of
``virtual_network_network_id`` property from virtual network in TF).

Expected switch configuration looks like (on QFX)::

    admin@qfx> show configuration interfaces xe-0/0/1 | display inheritance no-comments
    flexible-vlan-tagging;
    mtu 9192;
    encapsulation extended-vlan-bridge;
    unit 251 {
        vlan-id 251;
    }

    admin@qfx> show configuration vlans | display inheritance no-comments
    bd-8 {
        vlan-id none;
        interface xe-0/0/1.251;
        vxlan {
            vni 8;
        }
    }

.. note::

    This is only an example of possible configuration. Config is being managed by
    Device Manager and results depend on DM settings and possibilities.

.. tip::

    If right VMI is created in API but after a while there occurs no config changes
    on device, check Device Manager logs.


Known limitations
=================

There is a few not supported cases:
    * when network change VLAN tag, existing VMI are not updated,
