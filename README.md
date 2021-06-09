# MikroTik RouterOS SSH connector for Python

<div>
    <a href="https://github.com/d4vidcn/routeros_ssh_connector/blob/master/LICENSE"><img src="https://svgshare.com/i/Xt6.svg" /></a>
    <img src="https://svgshare.com/i/XtH.svg" />
</div>

## Features
A python-based SSH API for MikroTik devices

This API allows you to get, update and create configuration on MikroTik devices plus other some extra utilities.

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

**GET**                     |           **UPDATE**          |         **CREATE**        |      **TOOLS**
:--------------------------:|:-----------------------------:|:-------------------------:|:-------------------:
get_export_configuration    | update_address_pool           | create_address_pool       | configure_wlan
get_identity                | update_dhcp_client            | create_dhcp_client        | download_backup
get_interfaces              | update_dhcp_server_network    | create_dhcp_server        | download_export
get_ip_addresses            | update_dhcp_server_server     | create_ip_address         | download_file
get_resources               | update_identity               | create_route              | enable_cloud_dns
get_routes                  | update_ip_address             | create_user               | make_backup
get_services                | update_services               |                           | reboot_device
get_users                   | update_user                   |                           | send_command
.                           |                               |                           | update_system
.                           |                               |                           | upload_file


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

Output returns `True` if no errors are encountered. In other case, returns the error itself:

    True

#### Create a new enabled route to 172.16.0.0/25 with gateway 192.168.1.1 and distance of 5
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.create_route("172.16.0.0/25", "192.168.1.1", "5"))

router.disconnect()
del router
```

Output returns `True` if no errors are encountered. In other case, returns the error itself:

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

Output returns command output without left spaces (left trim):

    time: 19:47:44
    date: jun/01/2021
    time-zone-autodetect: yes
    time-zone-name: Europe/Madrid
    gmt-offset: +02:00
    dst-active: yes

#### Download backup from device to local folder
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")

# local_path examples:
# For Linux: "/home/myuser"
# For Windows: "C:/Users/myuser/Downloads"

print(router.download_backup("/home/myuser"))
router.disconnect()
del router
```

Output returns a message with full path of downloaded export file:

    /home/mysuser/backup_Mikrotik_07-06-2021_21-38-47.backup


#### Export full config from device to terminal output
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.get_export_configuration())
router.disconnect()
del router
```

Output returns device config export to terminal:

    # jun/01/2021 19:04:03 by RouterOS 6.47.9
    # software id = XXXX-XXXX
    #
    # model = RouterBOARD mAP L-2nD
    # serial number = FFFFFFFFFFF
    /interface pwr-line set [ find default-name=pwr-line1 ] disabled=yes
    /interface bridge add name=lo0
    /interface ethernet set [ find default-name=ether1 ] l2mtu=2000
    /interface wireless set [ find default-name=wlan1 ] ssid=MikroTik
    /interface wireless security-profiles set [ find default=yes ] supplicant-identity=MikroTik
    /ip hotspot profile set [ find default=yes ] html-directory=flash/hotspot
    ...

#### Export full config from device to local folder
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.download_export("/home/myuser"))
router.disconnect()
del router
```

Output returns a message with full path of downloaded export file:

    /home/myuser/export_Mikrotik_07-06-2021_21-42-33.rsc

#### Download any file from device
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.download_file("myfile.txt", "/home/myuser"))
router.disconnect()
del router
```

Output returns a message with full path of downloaded export file:

    /home/myuser/myfile.txt


#### Configure 2.4 GHz wlan interface
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.config_wlan(ssid="MySSID", password="12345678", band="2g"))
router.disconnect()
del router
```

Output returns a message with configuration result:

    2.4 GHz wlan configured sucessfully!


#### Upgrade RouterOS software
```python
from routeros_ssh_connector import MikrotikDevice

router = MikrotikDevice()
router.connect("10.0.0.1", "myuser", "strongpassword")
print(router.update_system())
router.disconnect()
del router
```

Output returns a message with command result:

    Update available!. Updating RouterOS device...
