============
ironic-proxy
============

Experimental proxy for Bare Metal API.

* Free software: Apache license
* Source: https://github.com/dtantsur/ironic-proxy

.. warning:: This is a proof-of-concept. DO NOT USE IN PRODUCTION!

Overview
========

The proxy works by delegating requests to remove Ironic instances,
distinguished by a *conductor group*:

* When creating a node, it's conductor group (defaulting to the empty string)
  is used to find the target installation.

* When doing actions on an existing node, the node is found by polling all
  sources. The node-to-group mapping is then cached for the runtime of
  the service.

* When listing all nodes, the listings from all sources are merged.

Status
------

Implemented API:

* Version discovery.
* Node creating, listing, getting and deleting.

Pretends to support the set of microversions common between all sources.

Authentication: **NO**

Architecture
------------

This one of the possible *Edge* architectures with *ironic-proxy*:

::

                             baremetal API    image API
                                  +               +
            Hub                   |               |
            +------------------------------------------+
            |                     |               |    |
            |                     v               v    |
            | keystone <---+ ironic-proxy +---> glance |
            |                   +                 ^    |
            +------------------------------------------+
                                |                 |
       +<------------+<---------+  +------------->+
       |             |             |
 +-------------------------------------+ +-------------------------------------+
 |     |             |             |   | |                                     |
 |     v             v             +   | |                                     |
 | keystone <---+ ir-api +---> ir-cond | | keystone <---+ ir-api +---> ir-cond |
 |                   ^            ^    | |                                     |
 |    local DHCP     |            |    | |                                     |
 |        ^          |            |    | |                                     |
 +-------------------------------------+ +-------------------------------------+
 Edge     |          |            |      Edge
          +<-------+ | +--------->+
                   | | |
       +-------+ +-+-+-+-+ +-------+          +-------+ +-------+ +-------+
       |       | |       | |       |          |       | |       | |       |
       +-------+ +-------+ +-------+          +-------+ +-------+ +-------+
       Nodes                                  Nodes

Notes:

* The *Hub* and *Edge* locations do not share message queue and database.

* The Network service (neutron) is not present, since it would require
  stretching message queue and database between the locations. Instead,
  a local DHCP server is used, and ironic is configured with the *noop* network
  interface.

  .. note::
      A tool like cloud-init or os-net-config_ can be used for post-deploy
      networking configuration.

* The Compute service (nova) can be used in theory, but its dependency on
  neutron is an issue. Neutron can be deployed and used by nova, but no
  networking configuration will be coming from it.

  The Metadata API cannot be used, a *configdrive* must be used instead.

* Each location has its own Identity service (keystone) installation.

* However, ironic-conductor at each *Edge* is configured to access the Image
  service (glance) at the *Hub* location.

  .. note::
      This is possible because ironic configures credentials for each service
      it uses separately.

  With the *iscsi* deploy interface, images will be served from the
  *ironic-conductor* location via iSCSI.

  With the *direct* deploy interface, ironic has to be configured with
  ``image_download_source=http`` to make sure images are served from the local
  HTTP server.

Configuration
=============

First, map all possible conductor groups to *sources*:

.. code-block:: ini

   [DEFAULT]
   groups = _:loc1,grp1:loc2,grp2:loc1

This maps the default group and group ``grp2`` to location ``loc1``, while the
group ``grp1`` is mapped to ``loc2``.

.. note:: The default group is designated as the underscore.

Then define the credentials to access every location, for example:

.. code-block:: ini

   [group:loc1]
   auth_type = password
   auth_url = http://192.168.42.1/identity
   username = ironic
   user_domain_id = default
   password = pa$$w0rd
   project_name = service
   project_domain_id = default

Running
=======

The proxy currently only consists of only one WSGI service. You can run it with
non-production development server via::

   tox -evenv -- python -m ironic_proxy.api --config-file /path/to/config/file

.. _os-net-config: https://github.com/openstack/os-net-config
