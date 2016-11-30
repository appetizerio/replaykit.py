import os

from setuptools import setup
VERSION = (1, 0, 0)
__version__ = '.'.join((str(x) for x in VERSION))

setup(
    name='appetizer',
    version=__version__,
    description='Appetizer tools for test recording, replaying and functional testing',
    author='Mingyuan Xia',
    author_email='mxia@mxia.me',
    url='https://github.com/appetizerio/appetizer-toolkit-py',
    license='Apache v2',
    packages=['appetizer'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
