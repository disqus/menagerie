menagerie
=========

    *menagerie* - (n.) a place where animals are kept and trained especially for exhibition

A ZooKeeper-backed Django settings holder.

Basic Usage
-----------

The ``menagerie.configure`` helper function provides a method to bootstrap your
Django settings using the settings already available by normal methods (via the
``DJANGO_SETTINGS_MODULE`` environment variable), but uses the settings present
in ZooKeeper to override these defaults.

To configure your application,

* Add a ``ZOOKEEPER_HOSTS`` setting to your Django settings file(s) that
  includes the network addresses of the ZooKeeper ensemble members to connect
  to as a list or tuple. For example:

  .. code:: python

      ZOOKEEPER_HOSTS = ('zookeeper-1.local', 'zookeeper-2.local')

  To bind the ZooKeeper client to a namespace other than the root namespace,
  add a ``ZOOKEEPER_SETTINGS_NAMESPACE`` setting containing the namespace.

* Add the following to the entry point(s) to your application (e.g.
  ``manage.py``) before accessing any attributes of ``django.conf.settings``:

  .. code:: python

      import menagerie
      menagerie.configure()

  It may be helpful to configure your logging to output ``DEBUG``-level
  messages for the ``menagerie`` namespace to track down any errors you may
  encounter when configuring your application.

Storage
-------

The settings storage is designed to be as simple as possible, and only uses the
nodes within a single tree to represent all settings.

Trees are not traversed recursively -- all settings must be stored as the
direct children of a shared root node, which defaults to ``/`` or the root of
your ZooKeeper cluster/client namespace.

For example, the following tree of node names and values in ZooKeeper::

    /DEBUG: true
    /INTERNAL_IPS: ['127.0.0.1', '192.168.0.1']

...would yield the following settings::

    settings.DEBUG == True
    settings.INTERNAL_IPS == ['127.0.0.1', '192.168.0.1']

The deserializer doesn't do any sort of merging of complex types such as
mappings or sequences -- either the values read from the ZooKeeper node data
will be returned, or the default value if no value exists in the ZooKeeper
tree.

Setting names that are valid as ZooKeeper node names but have language-specific
semantics in Python (for example, names containing the ``.`` or ``-``
characters) may still be used, but will need to be accessed using ``getattr``
on the settings holder, like so:

.. code:: python

    getattr(settings, 'MY-SPECIAL-SETTING')

Running Tests
-------------

The test suite can be run with ``make test``.

The suite requires a working ZooKeeper installation, the path to which can be
specified with the ``ZOOKEEPER_PATH`` environment variable. If you don't
already have an installation of ZooKeeper, running ``make zookeeper`` will
create one where the default path is located.
