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
