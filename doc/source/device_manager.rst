===============================
Integration with Device Manager
===============================

Networking-opencontrail supports integration with Device Manager from
Tungsten Fabric. It allows to automatically configure VLAN tags and VXLAN on
switches connected to computes, when virtual machine is plugged into a VLAN
network.

Configuration
=============

Prerequisites
-------------

* Encapsulation priorities in vrouter should be set with ``VXLAN`` on the
  first place.
* Fabric (including discovering switches) should be onboarded and Device
  Manager should be allowed to manage them.

.. seealso::

    To see details about fabric configuration and onboarding, see Juniper
    documentation, e.g. `Fabric Management <fabric_doc_>`_.

    .. _fabric_doc: https://www.juniper.net/documentation/en_US/contrail5.0/topics/task/configuration/ems-capabilities-on-physical-network-elements.html#id-fabric-management


Describing topology
-------------------

As written above, topology includes list of compute hosts and their connections
to switches. Integration with Device Manager will be provided only for listed
computes and there will be no impact for other hosts.

To describe topology, Tungsten Fabric API is used. Each ``node`` should represent a single compute host and
have refs to their ``ports``, which should be connected to related ``physical interfaces``.

Changes made using API are applied immediately. At this moment, no changes have any impact
on existing VM connections.

.. important::

    The name of node must be the same as compute name used by Open Stack.
    Integration is only triggered when compute name matches to one of the nodes
    in topology.

Usage
=====

When a virtual machine on one of the managed computes is connected to a VLAN network,
the plugin creates an additional VMI in Tungsten Fabric API, which then triggers Device
Manager to configure VLAN tagging on all switch ports connected to this host
and related VXLAN. When no VM in a VLAN network runs on the compute,
the VLAN tagging should be removed for this host.

.. note::

    Plugin only creates and removes VMI in Tungsten Fabric. Any other actions,
    particularly pushing configuration to the switches is done by Device Manager,
    which is required to configure them properly. You can read more about what the plugin
    does on the page :doc:`architecture/dm_integration`.
