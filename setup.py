import re

from setuptools import setup

version = ""

# I actually took it from requests library
with open('vk_api/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise ValueError("No version specified.")

setup(name='vk_api',
      version=version,
      description='VK API handler implementation',
      url='none',
      author='MrLokans',
      author_email='mrlokans@gmail.com',
      license='MIT',
      packages=['vk_api'],
      zip_safe=False,
      install_requires=['requests>=2.4.3']
      )
