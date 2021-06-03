# MikroTik RouterOS SSH connector for Python

## Features
A python-based SSH class for MikroTik devices

This class allows you to get, update and create configuration on MikroTik devices plus other some extra utilities.

This project is still in development and will include new functionalities in the future.

***

## Installation
    pip install routeros_ssh_connector


## Usage

#### 1. Import module
```python
from routeros_ssh_connector import MikrotikDevice
```

#### 2.  Create a new instance of them
```python
router = MikroTikDevice()
```

#### 3.  Connect to device
```python
router.connect("ip_address", "username", "password", "port")
```
> NOTE: If 'port' parameter is not passed to method the default value is 22

#### 4. Call any of the following available methods

**GET**             |    **UPDATE**     |      **CREATE**       |      **TOOLS**
:------------------:|:-----------------:|:---------------------:|:-------------------:
get_identity        | update_identity   | create_ip_address     | do_backup
get_interfaces      | update_ip_address | create_route          | enable_cloud_dns
get_ip_addresses    | update_services   | create_user           | export_configuration
get_resources       | update_user       |                       | send_command
get_routes<sup>**1**</sup>|                   |                       | 
get_services        |                   |                       | 
get_users           |                   |                       |

<sup>**1**</sup> Limited to first 1000 routes due to performance

```python
interfaces = router.get_interfaces()
print(interfaces)
```

#### 5.  Disconnect from device
```python
router.disconnect()
```

#### 6.  Delete `router` object (optional)
```python
del router
```
***

## Examples

#### Get interfaces from device
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword", 2222)
interfaces = router.get_interfaces()
print(interfaces)

router.disconnect()
del router
```
Output returns a list containing so many dictionaries as interfaces are found in device :

    [{'status': 'running', 'name': 'ether1', 'default-name': 'ether1', 'type': 'ether', 'mtu': '1500', 'mac_address': 'AA:BB:CC:DD:EE:F0'}, {'status': 'disabled', 'name': 'pwr-line1', 'default-name': 'pwr-line1', 'type': 'ether', 'mtu': '1500', 'mac_address': 'AA:BB:CC:DD:EE:F1'}, {'status': 'disabled', 'name': 'wlan1', 'default-name': 'wlan1', 'type': 'wlan', 'mtu': '1500', 'mac_address': 'B8:69:F4:07:BE:AD'}, {'status': 'running', 'name': 'lo0', 'type': 'bridge', 'mtu': '1500', 'mac_address': 'AA:BB:CC:DD:EE:F2'}]

#### Update FTP service to enable it, set port to 2121 and allow connections only from 192.168.1.0/24 subnet
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword", 2222)
print(router.update_services("ftp", "no", "2121", "192.168.1.0/24"))

router.disconnect()
del router
```

Output return `True` if no errors are encountered. In other case, returns the error itself:

    True

#### Create a new enabled route to 172.16.0.0/25 with a distance of 5 with gateway 192.168.1.1
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.create_route("172.16.0.0/25", "192.168.1.1", "5", "no"))

router.disconnect()
del router
```

Output return `True` if no errors are encountered. In other case, returns the error itself:

    True

#### Send custom command to device
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.send_command("/system clock print"))

router.disconnect()
del router
```

Output returns command output like a terminal:

                    time: 19:47:44
                    date: jun/01/2021
    time-zone-autodetect: yes
        time-zone-name: Europe/Madrid
            gmt-offset: +02:00
            dst-active: yes