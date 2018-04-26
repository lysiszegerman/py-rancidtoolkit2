#!/usr/bin/env python

from setuptools import setup, find_packages
import os
import sys

version = "0.3"

if sys.argv[-1] == 'publish':
    os.system('python3 setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

setup(name='rancidtoolkit2',
      version=version,
      description='Functions to parse network devices config files and output \
specific data',
      author='Marcus Stoegbauer',
      author_email='lysis@lys.is',
      license='MIT',
      packages=find_packages(),
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python"
                   ],
      install_requires=['requests', 'ipaddress'],
      zip_safe=False)
