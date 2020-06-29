from setuptools import setup
import ast
import sys

setup_requires = ['setuptools >= 30.3.0']

if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')


setup(description="integral-client",
      long_description=open('README.md').read(),
      version='1.1.6',
      include_package_data=True,
      setup_requires=setup_requires)
