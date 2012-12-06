import functools
import json
import logging
import posixpath

from django.conf import global_settings


logger = logging.getLogger(__name__)


_UNSET = object()


class NotConnectedError(Exception):
    pass


class ZooKeeperSettingsHolder(object):
    def __init__(self, zookeeper, path='/', defaults=None, start=True):
        if defaults is None:
            defaults = global_settings

        self.__zookeeper = zookeeper
        self.__path = path
        self.__defaults = defaults

        self.__settings = {}
        self.__stopping = True
        if start:
            self.start()

    def __getattr__(self, name):
        value = self.__settings.get(name, _UNSET)
        if value is not _UNSET:
            return value
        else:
            return getattr(self.__defaults, name)

    @property
    def running(self):
        """
        Whether the holder is currently observing changes.
        """
        return not self.__stopping

    def start(self):
        """
        Start observing settings changes.
        """
        if not self.__zookeeper.connected:
            raise NotConnectedError

        if self.running:  # ensures the holder is reentrant
            return

        self.__stopping = False
        self.__zookeeper.ChildrenWatch(self.__path)(self.__update_children)
        logger.info('Starting to observe settings changes...')

    def stop(self):
        """
        Stop observing settings changes.
        """
        self.__stopping = True
        logger.info('Stopping observing settings changes...')

    def __deserialize(self, value):
        return json.loads(value)

    def __update_node(self, node, data, stat):
        if not self.running:
            return False

        if data is None and stat is None:
            logger.info('Removing setting: %s', node)
            del self.__settings[node]
        else:
            value = self.__deserialize(data)
            logger.info('Updating setting: %s, new value is %r', node, value)
            self.__settings[node] = value

    def __update_children(self, children):
        if not self.running:
            return False

        for node in set(children) - set(self.__settings.keys()):
            path = posixpath.join(self.__path, node)
            callback = functools.partial(self.__update_node, node)
            logger.debug('Beginning to observe setting: %s', node)
            self.__zookeeper.DataWatch(path)(callback)
