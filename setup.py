from distutils.core import setup
from os import read

setup(
    name = 'routeros_ssh_connector',
    packages = ['routeros_ssh_connector'],
    version = '1.0',
    description = 'A python-based SSH class for MikroTik devices',
    author = 'd4vidCN',
    author_email = 'd4vidcn.code@gmail.com',
    license="MIT",
    url = 'https://github.com/d4vidcn/routeros_ssh_connector',
    download_url = 'https://github.com/d4vidcn/routeros_ssh_connector/tarball/v1.0',
    keywords = ['mikrotik', 'routeros', 'ssh', 'connector', 'ssh connector', 'mikrotik routeros', 'mikrotik ssh', 'routeros ssh'],
    classifiers = [],
    include_package_data = True,
    install_requires=[
          'netmiko==3.4.0',
      ],
)