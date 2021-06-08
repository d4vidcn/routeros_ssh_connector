from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = 'routeros_ssh_connector',
    packages = ['routeros_ssh_connector'],
    version = '1.6',
    description = 'A python-based SSH API for MikroTik devices',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author = 'd4vidCN',
    author_email = 'd4vidcn.code@gmail.com',
    license="MIT",
    url = 'https://github.com/d4vidcn/routeros_ssh_connector',
    project_urls={
        "Bug Tracker": "https://github.com/d4vidcn/routeros_ssh_connector/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords = ['mikrotik', 'routeros', 'ssh', 'connector', 'ssh connector', 'mikrotik routeros', 'mikrotik ssh', 'routeros ssh'],
    include_package_data = True,
    install_requires=[
          'netmiko==3.4.0',
      ]
)