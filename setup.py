from distutils.core import setup
from os import read

readme = open("README.md", "r")

setup(
    name = 'routeros_ssh_connector',
    packages = ['routeros_ssh_connector'],
    version = '1.1',
    description = 'A python-based SSH class for MikroTik devices',
    long_description = readme.read(),
    long_description_content_type = "text/markdown",
    author = 'd4vidCN',
    author_email = 'd4vidcn.code@gmail.com',
    license="MIT",
    url = 'https://github.com/d4vidcn/routeros_ssh_connector',
    keywords = ['mikrotik', 'routeros', 'ssh', 'connector', 'ssh connector', 'mikrotik routeros', 'mikrotik ssh', 'routeros ssh'],
    classifiers = [],
    include_package_data = True,
    install_requires=[
          'netmiko==3.4.0',
      ],
)