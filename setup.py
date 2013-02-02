import sys
from setuptools import find_packages, setup

try:
    import multiprocessing  # noqa
except ImportError:
    pass


install_requires = [
    'Django>=1.2,<1.5',
    'kazoo>=0.5,<0.9',
]

tests_require = [
    'exam==0.6.2',
    'nose',
    'unittest2',
]

setup_requires = []
if 'nosetests' in sys.argv[1:]:
    setup_requires.append('nose')

setup(
    name='menagerie',
    version='0.1.0',
    url='http://github.com/disqus/menagerie',
    author='ted kaemming, disqus',
    author_email='ted@disqus.com',
    packages=find_packages(exclude=('tests',)),
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    test_suite='nose.collector',
    license='Apache License 2.0',
    zip_safe=False,
)
