from setuptools import setup
import ast
import sys

setup_requires = ['setuptools >= 30.3.0', 'setuptools-git-version']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')


setup(description="integral client",
      long_description=open('README.md').read(),
      version_format = '{tag}.dev{commitcount}+{gitsha}', 
      setup_requires=setup_requires)
