============
Contributing
============
.. include:: ../../CONTRIBUTING.rst

Development guide
-----------------
Useful resources:

* `Gerrit`_
* `Git`_

.. _Gerrit: https://review.openstack.org/#/q/project:openstack/networking-opencontrail
.. _Git: https://git.openstack.org/cgit/openstack/networking-opencontrail

Running unit tests (in project directory)::

    tox -e py27

Running PEP8 checker (in project directory)::

    tox -e pep8

Generating coverage reports::

    tox -e cover

Generating docs::

    tox -e docs

Setting up test environment
---------------------------
We have prepared ansible scripts for setup of test environment which you may find helpful.

Then follow the guide available in :doc:`installation/playbooks`


Integration tests (non-voting currently)
-----------------------------------------
Integration tests check how NTF integrates with Neutron and TF.
Tests trigger specific actions (like network/port creation) in Neutron and then check
the expected objects were created/modified/deleted in TF Config API.

Running integration tests requires:

* Openstack controller (also it can be devstack) instance with keystone and neutron server
* TF controller with Config API on it
* Installed NTF on neutron-server connected to TF controller

Before it some env variables needs to be exported (on machine where tests run).
Full list of supported variables with default value (if any):

* CONTRAIL_IP=localhost - address IP of Contrail Controller
* CONTROLLER_IP=localhost - address IP of Openstack controller, used only for devstack installation
* OS_AUTH_URL - keystone auth url for Openstack used for non devstack installation in format:
    http(s)://(openstack_ip):5000/v3
* KEYSTONE_USER=admin
* KEYSTONE_PASSWORD=admin
* KEYSTONE_PROJECT=admin
* KEYSTONE_PROJECT_DOMAIN_ID=default
* KEYSTONE_USER_DOMAIN_ID=default
* PROVIDER=public - name of physical network in Openstack which will be used for VLAN network
    creation

Then, run integration tests(in project directory)::

    stestr -c networking_opencontrail/tests/integration/.stestr.conf run --concurrency=1

Changes standards
---------------------------
Every proposed change should fulfill below conditions:


Coding:

* Every added major class/function has descriptive docstring
* Every added test class has descriptive docstring
* PEP8 compliance

Architectural:

* repository module is a only place responsible for saving TF objects using TF client
* resource module is a only place responsible for creating and deleting TF objects
* Only TF client has rights to add ML2 tag
* Only TF client has rights for filtering TF objects by ML2 tag
* Repository has only rights for checking that given TF object has ML2 tag
