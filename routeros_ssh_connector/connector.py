import re, time, paramiko, tempfile, os, sys, paramiko

from datetime import datetime
from netmiko import Netmiko
from packaging.version import Version, parse

class MikrotikDevice:
    def __init__(self):
        self.now = datetime.now()
        self.current_datetime = self.now.strftime("%d-%m-%Y_%H-%M-%S")
        self.last_backup = {}
        self.last_export = {}
        self.tempdir = tempfile.gettempdir().replace("\\", "/") + "/"


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Connection methods
    def connect(self, ip_address, username, password, port=22):
        self.device = {
            "host": ip_address,
            "username": username,
            "password": password,
            "device_type": "mikrotik_routeros",
            "port": port,
        }
        try:
            self.net_connect = Netmiko(**self.device, global_cmd_verify=False, global_delay_factor=2, conn_timeout=5)

        except Exception as e:
            if "TCP connection to device failed" in str(e):
                print("ERROR: No response from device. Check device connection parameters")
                sys.exit()

            elif "Authentication to device failed" in str(e):
                print("ERROR: Authentication failed. Check username and password")
                sys.exit()
                
            else:
                print("EXCEPTION:", str(e))
                sys.exit()

    def disconnect(self):
        self.net_connect.disconnect()


 # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> GET methods
    def get_export_configuration(self):
        self.output = self.net_connect.send_command("/export terse", delay_factor=8)    

        output = ""    

        for line in self.output.splitlines():
            if line != "":
                if output == "":
                    output += line
                else:
                    output += "\n" + line
        
        return output

    def get_identity(self):
        self.output = self.net_connect.send_command("/system identity print")        

        for line in self.output.splitlines():            
            parsed = re.sub(" +", "", line).strip().split(":")

            if parsed != "":
                return parsed[1]

    def get_interfaces(self):
        return self.parse_interfaces(self.net_connect.send_command("/interface print detail without-paging"))

    def get_ip_addresses(self):
        self.ip_addresses = []

        self.output = self.net_connect.send_command("/ip addr print without-paging")        

        for line in self.output.splitlines():
            ip_address = {}
            parsed = re.sub(" +", " ", line).strip().split(" ")

            if re.search("^([0-9]|[1-9][0-9]{1,2}|[1-7][0-9]{3}|80[0-9]{2}|81[0-8][0-9]|819[0-2])", parsed[0]):
                if re.search("[A-Z]", parsed[1]):
                    ip_address["address"] = parsed[2]
                
                else:
                    ip_address["address"] = parsed[1]

                ip_address["network"] = parsed[2]
                ip_address["interface"] = parsed[3]
                self.ip_addresses.append(ip_address)

        return self.ip_addresses

    def get_resources(self):
        self.resources = {}
        self.output = self.net_connect.send_command("/system resource print")        

        for line in self.output.splitlines():            
            parsed = line.replace(": ", ":").replace("MiB", " MiB").replace("KiB", " KiB").replace("MHz", " MHz").replace("%", " %").strip().split(":")

            if parsed[0] != "":
                if parsed[0] == "uptime":
                    parsed[1] = parsed[1].replace("y", "y ").replace("w", "w ").replace("d", "d ").replace("h", "h ").replace("m", "m ")
                    self.resources[parsed[0]] = parsed[1]

                if parsed[0] == "build-time":
                    self.resources[parsed[0]] = parsed[1] + ":" + parsed[2] + ":" + parsed[3]

                else:
                    self.resources[parsed[0]] = parsed[1]

        return self.resources

    def get_routes(self):
        print("*** INFO ***: This process may take some time to get info depending on how many routes have in your device. Please wait...")

        self.routes = []
        filename = f"routes_{self.get_identity()}.txt"
        delay = 0

        total_routes = int(self.net_connect.send_command(f"/ip route print count-only"))

        if total_routes <= 500:
            delay = 4
        
        elif total_routes <= 1500:
            delay = 8
        
        elif total_routes <= 2500:
            delay = 16

        elif total_routes > 2500:
            delay = 32

        self.net_connect.send_command(f"/ip route print detail terse without-paging file={filename}", delay_factor=delay)
        self.download_file(filename, self.tempdir)

        routes = open(self.tempdir + filename, "r")

        for line in routes:
            parsed = re.sub(" +", " ", line).strip()            

            if re.search("^([0-9]|[1-9][0-9]{1,5}|[1-7][0-9]{6}|8000000)", parsed):
                route = {}

                route_line = parsed.split(" ")
                
                route['flags'] = route_line[1]
                route["destination"] = re.search(r'dst-address=(.*?) [a-z]', parsed).group(1)

                if "gateway" in parsed:
                    route["gateway"] = re.search(r'gateway=(.*?) [a-z]', parsed).group(1)
                else:
                    route["gateway"] = ""

                route["distance"] = re.search(r'distance=(.*?) [a-z]', parsed).group(1)
                
                self.routes.append(route)

        self.net_connect.send_command(f"/file remove {filename}")

        routes.close()
        os.remove(self.tempdir + filename)

        return self.routes

    def get_services(self):
        self.services = []        

        self.output = self.net_connect.send_command("/ip service print without-paging")        

        for line in self.output.splitlines():
            service = {}

            parsed = re.sub(" +", " ", line).strip().split(" ")            

            if re.search("^([0-9]|1[0-9]|2[0-9])", parsed[0]):
                if re.search("[XI]", parsed[1]):
                    service["name"] = parsed[2]
                    service["port"] = parsed[3]
                    if len(parsed) > 4:
                        service["address"] = parsed[4]
                else:
                    service["name"] = parsed[1]
                    service["port"] = parsed[2]
                    if len(parsed) > 3:
                        service["address"] = parsed[3]
                
                self.services.append(service)

        return self.services

    def get_users(self):
        self.users = []

        self.output = self.net_connect.send_command("/user print")        

        for line in self.output.splitlines():
            user = {}
            parsed = re.sub(" +", " ", line).strip().split(" ")

            if re.search("^([0-9]|1[0-9]|2[0-9])", parsed[0]):
                user["username"] = parsed[1]
                user["group"] = parsed[2]            
                self.users.append(user)

        return self.users        


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> UPDATE methods
    def update_address_pool(self, pool_name, new_pool_name=None, addresses=None, next_pool=None):
        self.cmd = f"/ip pool set {pool_name}"

        if new_pool_name is not None:
            self.cmd += f" name={new_pool_name}"

        if addresses is not None:
            self.cmd += f" ranges={addresses}"

        if next_pool is not None:
            self.cmd += f" next-pool={next_pool}"

        return self.check_result(self.net_connect.send_command(self.cmd))

    def update_dhcp_client(self, interface, disabled, add_default_route, route_distance, use_peer_dns, use_peer_ntp):
        return self.check_result(self.net_connect.send_command(f"/ip dhcp-client set numbers=[find interface=\"{interface}\"] disabled={disabled} add-default-route={add_default_route} default-route-distance={route_distance} use-peer-dns={use_peer_dns} use-peer-ntp={use_peer_ntp}"))

    def update_dhcp_server_server(self, interface, disabled=None, name=None, lease_time=None, address_pool=None):
        self.cmd = f"/ip dhcp-server set numbers=[find interface=\"{interface}\"]"

        if disabled is not None:
            self.cmd += f" disabled={disabled}"

        if name is not None:
            self.cmd += f" name={name}"

        if lease_time is not None:
            self.cmd += f" lease-time={lease_time}"

        if address_pool is not None:
            self.cmd += f" address-pool={address_pool}"

        return self.check_result(self.net_connect.send_command(self.cmd))

    def update_dhcp_server_network(self, address, gateway=None, netmask=None, dns_server=None, ntp_server=None):
        get_networks = self.net_connect.send_command("/ip dhcp-server network print")

        network_match = False
        network_count = 0

        for network in get_networks.splitlines():
            parsed_line = re.sub(" +", " ", network).strip().split(" ")

            if re.search("^\d+", parsed_line[0]):
                network_count += 1

                if parsed_line[1] == address:
                    network_match = True

                    self.cmd = f"/ip dhcp-server network set numbers=[find address=\"{address}\"]"

                    if gateway is not None:
                        self.cmd += f" gateway={gateway}"

                    if netmask is not None:
                        self.cmd += f" netmask={netmask}"

                    if dns_server is not None:
                        self.cmd += f" dns-server={dns_server}"

                    if ntp_server is not None:
                        self.cmd += f" ntp-server={ntp_server}"                    

                    return self.check_result(self.net_connect.send_command(self.cmd))

        if network_count == 0:
            return "ERROR: There are not any created network. Please, create it first"

        if network_match == False:
            return "ERROR: There are not any network with specified address"

    def update_identity(self, name):
        return self.check_result(self.net_connect.send_command(f"/system identity set name={name}"))

    def update_ip_address(self, interface, address, disabled="no"):
        return self.check_result(self.net_connect.send_command(f"/ip address set address={address} disabled={disabled} [find interface=\"{interface}\"]"))

    def update_services(self, service, disabled, port=None, address=None):
        self.command = f"/ip service set {service} disabled={disabled}"

        if port != None:
            self.command += f" port={port}"
        
        if address != None:
            self.command += f" address={address}"

        return self.check_result(self.net_connect.send_command(self.command))

    def update_user(self, username, password, group):
        self.command = f"/user set {username}"        

        if password != "":
            self.command += f" password={password}"

        if group != "":
            self.command += f" group={group}"

        return self.check_result(self.net_connect.send_command(self.command))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CREATE methods
    def create_address_pool(self, name, range, next_pool="none"):
        return self.check_result(self.net_connect.send_command(f"/ip pool add name={name} ranges={range} next-pool={next_pool}"))

    def create_dhcp_client(self, interface, disabled="no", add_default_route="yes", route_distance=1, use_peer_dns="yes", use_peer_ntp="yes"):
        return self.check_result(self.net_connect.send_command(f"""
            /ip dhcp-client add interface=\"{interface}\" disabled={disabled} add-default-route={add_default_route} default-route-distance={route_distance} use-peer-dns={use_peer_dns} use-peer-ntp={use_peer_ntp}
            """))

    def create_dhcp_server(self, interface, network_address=None, disabled="no", name="dhcp_server", address_pool="static-only", lease_time="00:10:00", dns_server="1.1.1.1,9.9.9.9"):
        server_cmd = self.check_result(self.net_connect.send_command(f"/ip dhcp-server add disabled={disabled} interface=\"{interface}\" name={name} address-pool={address_pool} lease-time={lease_time}"))
        network_cmd = ""

        if server_cmd == True:
            ip_addresses = self.get_ip_addresses()
            available_ip_addresses = []
            
            for ip_address in ip_addresses:
                if ip_address['interface'] == interface:
                    available_ip_addresses.append(ip_address['address'])
                    
            if len(available_ip_addresses) == 1:
                network = ip_address['network']
                prefix = ip_address['address'].split("/")[1]
                address = network + "/" + prefix
                gateway = ip_address['address'].split("/")[0]
                
                network_cmd = self.check_result(self.net_connect.send_command(f"/ip dhcp-server network add address={address} gateway={gateway} dns-server={dns_server}"))

                if network_cmd is not True:
                    return network_cmd

            else:
                if network_address is not None:                    
                    network = ip_address['network']
                    prefix = ip_address['address'].split("/")[1]
                    address = network + "/" + prefix
                    gateway = ip_address['address'].split("/")[0]
                
                    network_cmd = self.check_result(self.net_connect.send_command(f"/ip dhcp-server network add address={address} gateway={gateway} dns-server={dns_server}"))

                    if network_cmd is not True:
                        return network_cmd
                    
                else:
                    err_msg = f"ERROR: There is more than one IP address assigned to the same interface. Run the command again and pass 'network_address' parameter with the IP address on which you want to configure the DHCP server."
                    print(err_msg, "\nAvailable IP addresses are:")

                    for ip in available_ip_addresses:
                        print(f"\t{ip}")

        else:
            return server_cmd

        if server_cmd == True and network_cmd == True:
            return True

    def create_ip_address(self, ip_address, interface):
        return self.check_result(self.net_connect.send_command(f"/ip address add address={ip_address} interface=\"{interface}\""))

    def create_route(self, dst_address, gateway, distance, disabled="no"):
        return self.check_result(self.net_connect.send_command(f"/ip route add dst-address={dst_address} gateway={gateway} distance={distance} disabled={disabled}"))

    def create_user(self, username, password, group):
        return self.check_result(self.net_connect.send_command(f"/user add name={username} password={password} group={group}"))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> TOOLS methods
    def configure_wlan(self, ssid, password, band, country="no_country_set"):
        self.net_connect.send_command(f"/interface wireless security-profiles remove auto_wlan")

        self.net_connect.send_command(f"/interface wireless security-profiles add name=auto_wlan mode=dynamic-keys authentication-types=wpa2-psk,wpa2-eap \
                                        unicast-ciphers=aes-ccm,tkip group-ciphers=aes-ccm,tkip wpa2-pre-shared-key={password}")

        self.net_connect.send_command("/int wi reset-configuration [find]")

        output = self.net_connect.send_command(f"/interface wireless print detail")
        ros_license_level = self.net_connect.send_command(f":put [/system license get nlevel]")

        if "input does not match" in ros_license_level:
            ros_license_level = self.net_connect.send_command(f":put [/system license get level]")

        radio_mode = None

        if int(ros_license_level) < 4:
            radio_mode = "bridge"
        else:
            radio_mode = "ap-bridge"     

        wlan_2g_index = None
        wlan_5g_index = None

        for line in output.splitlines():
            if line != "":
                if "name" in line:
                    interface_index = int(line.strip().split(" ")[0])
                    frequency = re.search(r"frequency=(.*?) [a-z]", line)
                    
                    if frequency:
                        if int(frequency.group(1)) in range (2000,3000):
                            wlan_2g_index = interface_index

                        elif int(frequency.group(1)) in range (5000,6000):
                            wlan_5g_index = interface_index

        query_cmd_2g = f"/interface wireless set {wlan_2g_index} disabled=no ssid={ssid} radio-name={ssid} mode={radio_mode} band=2ghz-b/g/n channel-width=20/40mhz-Ce \
            frequency=auto wireless-protocol=802.11 wps-mode=disabled frequency-mode=regulatory-domain country=no_country_set installation=indoor wmm-support=enabled \
                max-station-count=100 distance=indoors hw-retries=8"

        query_cmd_5g = f"/interface wireless set {wlan_5g_index} disabled=no ssid={ssid} radio-name={ssid} mode={radio_mode} band=5ghz-a/n channel-width=20/40mhz-Ce \
            frequency=auto wireless-protocol=802.11 wps-mode=disabled frequency-mode=regulatory-domain country=no_country_set installation=indoor wmm-support=enabled \
                max-station-count=100 distance=indoors hw-retries=8"

        if band == "2g":
            if wlan_2g_index != None:                
                output = self.net_connect.send_command(query_cmd_2g)
                        
                if "any value of country" in output:
                    return "ERROR: Invalid country name!"
                else:
                    return "2.4 GHz wlan configured sucessfully!"

            else:
                return "There aren't any 2.4 GHz wlan interface present"

        elif band == "5g":
            if wlan_5g_index != None:
                output = self.net_connect.send_command(query_cmd_5g)

                if "any value of country" in output:
                    return "ERROR: Invalid country name!"
                else:
                    return "5 GHz wlan configured sucessfully!"

            else:
                return "There aren't any 5 GHz wlan interface present"

        elif band == "both":
            if wlan_2g_index != None and wlan_5g_index != None:
                output2 = self.net_connect.send_command(query_cmd_2g)

                output5 = self.net_connect.send_command(query_cmd_5g)

                if "any value of country" in output2 or "any value of country" in output5:
                    return "ERROR: Invalid country name!"
                else:
                    return "2.4 and 5 GHz wlan configured sucessfully!"

            elif wlan_2g_index != None and wlan_5g_index == None:
                print("WARNING: There aren't any 5 GHz wlan interface present. Configuring 2.4 GHz wlan only")

                output = self.net_connect.send_command(query_cmd_2g)

                if "any value of country" in output:
                    return "ERROR: Invalid country name!"
                else:
                    return "2.4 GHz wlan configured sucessfully!"                

            elif wlan_2g_index == None and wlan_5g_index != None:
                print("WARNING: There aren't any 2.4 GHz wlan interface present. Configuring 5 GHz wlan only")

                self.net_connect.send_command(query_cmd_5g)

                if "any value of country" in output:
                    return "ERROR: Invalid country name!"
                else:
                    return "5 GHz wlan configured sucessfully!"

    def download_backup(self, local_path, filename=None):
        if filename == None:
            if self.make_backup():
                return self.download_file(self.last_backup['name'], local_path)
        else:
            return self.download_file(filename, local_path)

    def download_export(self, local_path):
        print("*** INFO ***: This process may take some time to get info depending on how many config are in your device. Please wait...")

        self.last_export['name'] = "export_" + self.get_identity() + "_" + self.current_datetime + ".rsc"
        self.net_connect.send_command(f"/export terse file={self.last_export['name']}", delay_factor=16)

        return self.download_file(self.last_export['name'], local_path)

    def download_file(self, filename, local_path):
        transport = paramiko.Transport((self.device['host'], self.device['port']))
        transport.connect(None, self.device['username'], self.device['password'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = "/" + filename
        local_path = local_path + f"/{filename}"

        try:
            sftp.stat(remote_path)
            sftp.get(remotepath=remote_path, localpath=local_path)
            
            return local_path

        except Exception as e:
            if "Errno 13" in str(e):
                print(f"ERROR: Permission denied in local folder {local_path}")
                return False

            elif "Errno 2" in str(e):
                print("ERROR: File '{}'not found. Please make sure that file exists in remote device".format(remote_path.replace("/", "")))
                return False

            else:
                print(f"ERROR: {e}")
                return False

    def enable_cloud_dns(self):
        self.net_connect.send_command("/ip cloud set ddns-enabled=yes")
        time.sleep(2)

        return self.net_connect.send_command(":put [/ip cloud get dns-name]")

    def make_backup(self, name="backup", password=None, encryption="aes-sha256", dont_encrypt="yes"):
        self.last_backup['name'] = name + "_" + self.get_identity() + "_" + self.current_datetime + ".backup"

        base_cmd = f"/system backup save name={self.last_backup['name']} encryption={encryption} dont-encrypt={dont_encrypt}"

        if password is not None:
            base_cmd += f" password={password}"
        
        self.output = self.net_connect.send_command(base_cmd, delay_factor=8)

        if "backup saved" in self.output:
            return True
        else:
            return False

    def reboot_device(self):
        filename = "reboot.auto.rsc"
        f = open(self.tempdir + filename, "w")
        f.write("/system reboot")
        f.close()

        if self.upload_file(self.tempdir, filename):
            os.remove(self.tempdir + filename)
            return True
        else:
            return False

    def send_command(self, query):
        output = ""

        for line in str(self.net_connect.send_command(query, delay_factor=8)).splitlines():
            if line != "":
                if output == "":
                    output += line.lstrip()
                else:
                    output += "\n" + line.lstrip()
        
        return output

    def update_system(self, channel="long-term"):
        print("Checking RouterOS updates...")
        self.net_connect.send_command(f"/system package update set channel={channel}")
        self.net_connect.send_command(f"/system routerboard settings set auto-upgrade=yes")        

        current_package_version = self.net_connect.send_command("/system package update print")

        current_version = ""

        for line in current_package_version.splitlines():
            if line != "":
                parsed_line = line.strip().replace(" ", "")

                if parsed_line.split(":")[0] == "installed-version":
                    current_version = Version(parsed_line.split(":")[1])

        self.net_connect.send_command("/system package update check-for-updates once")
        time.sleep(3)

        latest_version = Version(self.net_connect.send_command(":put [/system package update get latest-version]"))

        if latest_version > current_version:            
            self.net_connect.send_command("/system package update install")
            return "Update available!. Updating RouterOS device..."
        else:
            return "Device is up to date!"

    def upload_file(self, local_path, filename):
        transport = paramiko.Transport((self.device['host'], self.device['port']))
        transport.connect(None, self.device['username'], self.device['password'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = "/" + filename
        local_path = local_path + f"/{filename}"

        try:
            sftp.put(localpath=local_path, remotepath=remote_path)
            return True

        except Exception as e:
            print(f"ERROR: {e}")
            return False


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Auxiliary methods
    def check_result(self, command_output):
        for line in command_output.splitlines():
            message = re.sub(" +", " ", line).strip()

            if message != "":
                return message
            else:
                return True

    def parse_interfaces(self, raw_interfaces):
        self.interfaces = []

        for line in raw_interfaces.splitlines():
            interface = {}
            parsed = re.sub(" +", " ", line).strip()

            if re.search("^([0-9]|[1-9][0-9]{1,2}|[1-7][0-9]{3}|80[0-9]{2}|81[0-8][0-9]|819[0-2])", parsed):
                status = parsed.split(" ")[1]
                
                if status == "R":
                    status = "running"

                elif status == "X":
                    status = "disabled"

                elif status == "D":
                    status = "dynamic"

                elif status == "S":
                    status = "slave"

                elif status == "RS":
                    status = "running-slave"

                elif status == "XS":
                    status = "disabled-slave"

                elif status == "DRS":
                    status = "dynamic-running-slave"
                
                elif "name=" in status:
                    status = "not_connected"

                interface["status"] = status
                interface["name"] = re.search(r'name="(.*?)"', parsed).group(1)

                if "default-name" in parsed:
                    interface["default-name"] = re.search(r'default-name="(.*?)"', parsed).group(1)
                
                interface["type"] = re.search(r'type="(.*?)"', parsed).group(1)

                if "actual-mtu" in parsed:
                    interface["mtu"] = re.search(r"actual-mtu=(.*?) [a-z]", parsed).group(1)
                else:
                    interface["mtu"] = ""

                if "mac-address" in parsed:
                    interface["mac_address"] = re.search(r"mac-address=(.*?) [a-z]", parsed).group(1)
                else:
                    interface['mac_address'] = ""

                self.interfaces.append(interface)

        return self.interfaces
