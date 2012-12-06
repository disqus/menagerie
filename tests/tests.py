from __future__ import absolute_import

import json
import mock
import operator
import posixpath
import threading
import unittest2

from django.conf import global_settings, settings
from django.core.exceptions import ImproperlyConfigured
from exam import Exam, before, fixture
from kazoo.client import KazooClient
from kazoo.testing.harness import KazooTestCase

import menagerie
from menagerie.holder import NotConnectedError, ZooKeeperSettingsHolder


class TestCase(Exam, KazooTestCase, unittest2.TestCase):
    TIMEOUT = 5

    def get_child_node_event(self, path, comparator=operator.contains):
        event = threading.Event()
        node = posixpath.basename(path)

        def callback(children):
            success = comparator(children, node)
            if success:
                event.set()
            return not success

        self.client.ChildrenWatch(posixpath.dirname(path))(callback)
        return event


class ZooKeeperSettingsHolderTestCase(TestCase):
    @fixture
    def holder(self):
        """Returns an instantiated settings holder."""
        return ZooKeeperSettingsHolder(self.client, defaults=object())

    def test_client_must_be_connected(self):
        # Ensure the client must be connected to start the settings holder.
        client = KazooClient()
        self.assertFalse(client.connected)

        holder = ZooKeeperSettingsHolder(client, start=False)
        with self.assertRaises(NotConnectedError):
            holder.start()

    def test_attribute_access(self):
        # Ensure simple attribute access works, deserializing values from ZooKeeper.
        self.client.create('/DEBUG', json.dumps(True))
        self.assertTrue(self.holder.DEBUG)

    def test_updates_on_node_addition(self):
        # Ensure that nodes added after the holder has been instantiated are
        # accessible as attribute on the settings holder.
        with self.assertRaises(AttributeError):
            self.holder.DEBUG

        event = self.get_child_node_event('/DEBUG')
        self.client.create('/DEBUG', json.dumps(True))
        event.wait(self.TIMEOUT)
        self.assertTrue(self.holder.DEBUG)

    def test_updates_on_node_removal(self):
        # Ensure that nodes removed after the holder has been instantiated are
        # removed as attributes on the settings holder.
        self.client.create('/DEBUG', json.dumps(True))
        self.assertTrue(self.holder.DEBUG)  # sanity check

        event = self.get_child_node_event('/DEBUG',
            comparator=lambda *a: not operator.contains(*a))

        self.client.delete('/DEBUG')
        event.wait(self.TIMEOUT)
        with self.assertRaises(AttributeError):
            self.holder.DEBUG

    def test_updates_on_node_change(self):
        # Ensure that nodes updated after the holder has been instantiated are
        # updated as attributes on the settings holder.
        self.client.create('/DEBUG', json.dumps(True))
        self.assertTrue(self.holder.DEBUG)  # sanity check

        value = False

        event = threading.Event()

        def callback(data, stat):
            success = json.loads(data) == value
            if success:
                event.set()
            return not success

        self.client.DataWatch('/DEBUG')(callback)
        self.client.set('/DEBUG', json.dumps(value))
        event.wait(self.TIMEOUT)
        self.assertEqual(self.holder.DEBUG, value)


class DjangoIntegrationTestCase(TestCase):
    @before
    def reset_django_settings(self):
        # Ensure the settings are not configured.
        if settings.configured:
            try:
                from django.conf import empty
            except ImportError:
                empty = None  # noqa
            settings._wrapped = empty
            assert not settings.configured

    @fixture
    def holder(self):
        """Returns an instantiated settings holder."""
        return ZooKeeperSettingsHolder(self.client)

    def patch_test_settings(self):
        """
        Patches the test settings with the current ZooKeeper configuration from
        the Kazoo test harness.
        """
        import tests.settings
        hosts, namespace = self.hosts.split('/')
        hosts = hosts.split(',')

        tests.settings.ZOOKEEPER_HOSTS = hosts
        tests.settings.ZOOKEEPER_SETTINGS_NAMESPACE = namespace

    def set_node_and_assert_setting_updated(self, node, data, action='create'):
        method = '_ZooKeeperSettingsHolder__update_node'
        update = getattr(settings, method)

        with mock.patch.object(settings, method) as mock_update:
            expected = json.dumps(data)

            event = threading.Event()

            def monitor(*args):
                result = update(*args)
                if node == args[0] and expected == args[1]:
                    event.set()
                return result

            mock_update.side_effect = monitor
            getattr(self.client, action)('/%s' % node, expected)
            event.wait(self.TIMEOUT)
            self.assertEqual(getattr(settings, node), data)

    def test_explicit_configure(self):
        # Ensure settings configured in ZooKeeper are reflected in Django settings.
        self.client.create('/READONLY', json.dumps(True))
        self.assertTrue(self.holder.READONLY)  # sanity check
        settings.configure(self.holder)
        self.assertTrue(settings.READONLY)

    def test_overrides_global_settings(self):
        # Ensure that the global settings are used unless overriden.
        self.assertFalse(global_settings.DEBUG)  # sanity check
        settings.configure(self.holder)
        self.assertFalse(settings.DEBUG)

        event = self.get_child_node_event('/DEBUG')
        self.client.create('/DEBUG', json.dumps(True))
        event.wait(self.TIMEOUT)
        self.assertTrue(settings.DEBUG)

    def test_configure_helper_must_have_module(self):
        # Ensure the configuration helper requires a module to be provided.
        with self.assertRaises(ImproperlyConfigured):
            menagerie.configure()

        with self.assertRaises(ImportError):
            menagerie.configure('invalid.module')

    def test_configure_helper_uses_module_settings(self):
        # Ensure that the configuration helper adds both module and global
        # settings as default settings.
        self.patch_test_settings()

        menagerie.configure(module='tests.settings')

        # Ensure global settings are still used.
        self.assertEqual(settings.DEBUG, global_settings.DEBUG)

        # Ensure readonly from module settings is still applied.
        self.assertTrue(settings.READONLY)

        # Make sure global settings are still overridden.
        self.set_node_and_assert_setting_updated('DEBUG', True)

        # Make sure module settings are still overridden.
        self.set_node_and_assert_setting_updated('READONLY', False)

    def test_explicit_attributes_override_defaults(self):
        self.patch_test_settings()

        menagerie.configure(module='tests.settings')
        self.assertFalse(settings.DEBUG)

        sentinel = object()
        settings.DEBUG = sentinel
        self.assertIs(settings.DEBUG, sentinel)
