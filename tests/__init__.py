import os
import sys


def __patch_zookeeper_path(var='ZOOKEEPER_PATH', stream=sys.stderr):
    path = os.environ.get(var)
    if not path:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'vendor', 'zookeeper'))
        print >> stream, 'Patching unset %r to %r...' % (var, path)
        if not os.path.isdir(path):
            print >> stream, '\n', '*' * 70, '\n'
            print >> stream, 'ERROR: %r is not a directory!' % path
            print >> stream, 'To run the test suite, the environment variable ' \
                '%r must be set to the path of a valid ZooKeeper installation.' % var
            print >> stream, 'To install ZooKeeper, run `make zookeeper` from ' \
                'the project root directory.'
            print >> stream, '\n', '*' * 70, '\n'
            sys.exit(1)
        os.environ[var] = path


__patch_zookeeper_path()
