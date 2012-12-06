import logging
import os

from django.conf import ENVIRONMENT_VARIABLE, Settings, settings
from django.core.exceptions import ImproperlyConfigured
from kazoo.client import KazooClient

from menagerie.holder import ZooKeeperSettingsHolder


logger = logging.getLogger(__name__)


def configure(module=None, client=KazooClient, holder=ZooKeeperSettingsHolder):
    if module is None:
        try:
            module = os.environ[ENVIRONMENT_VARIABLE]
            if not module:
                raise KeyError
        except KeyError:
            raise ImproperlyConfigured('%s is not defined, cannot import settings')

    __settings = Settings(module)

    hosts = ','.join(__settings.ZOOKEEPER_HOSTS)
    if hasattr(__settings, 'ZOOKEEPER_SETTINGS_NAMESPACE'):
        hosts = '/'.join((hosts, __settings.ZOOKEEPER_SETTINGS_NAMESPACE))

    logger.debug('Attempting to connect to ZooKeeper at "%s"...', hosts)
    zookeeper = client(hosts=hosts)
    zookeeper.start()

    settings.configure(holder(zookeeper, defaults=__settings))
