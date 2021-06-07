from os import remove
import re
import time
import paramiko

from datetime import datetime
from netmiko import Netmiko
import paramiko

class MikrotikDevice:
    def __init__(self):
        self.now = datetime.now()
        self.current_datetime = self.now.strftime("%d-%m-%Y_%H-%M-%S")
        self.last_backup = {}


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def connect(self, ip_address, username, password, port=22):
        self.device = {
            "host": ip_address,
            "username": username,
            "password": password,
            "device_type": "mikrotik_routeros",
            "port": port,
        }
        self.net_connect = Netmiko(**self.device, global_cmd_verify=False, global_delay_factor=2)

    def disconnect(self):
        self.net_connect.disconnect()


 # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
        self.interfaces = []
        
        self.output = self.net_connect.send_command("/interface print detail without-paging")

        for line in self.output.splitlines():
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
        self.routes = []        

        self.output = self.net_connect.send_command("/ip route print detail without-paging")

        for line in self.output.splitlines():
            parsed = re.sub(" +", " ", line).strip()            

            if re.search("^([0-9]|[1-9][0-9]{1,5}|[1-7][0-9]{6}|8000000)", parsed):
                route = {}

                route_counter = int(parsed.split(" ")[0])

                if route_counter <= 1000:
                    route_line = parsed.split(" ")
                    
                    route['flags'] = route_line[1]
                    route["destination"] = re.search(r'dst-address=(.*?) [a-z]', parsed).group(1)

                    if "gateway" in parsed:
                        route["gateway"] = re.search(r'gateway=(.*?) [a-z]', parsed).group(1)
                    else:
                        route["gateway"] = ""

                    route["distance"] = re.search(r'distance=(.*?) [a-z]', parsed).group(1)
                    
                    self.routes.append(route)

                else:
                    break

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


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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

    def create_route(self, dst_address, gateway, distance, disabled):
        return self.check_result(self.net_connect.send_command(f"/ip route add dst-address={dst_address} gateway={gateway} distance={distance} disabled={disabled}"))

    def create_user(self, username, password, group):
        return self.check_result(self.net_connect.send_command(f"/user add name={username} password={password} group={group}"))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def check_result(self, command_output):
        for line in command_output.splitlines():
            message = re.sub(" +", " ", line).strip()

            if message != "":
                return message
            else:
                return True


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def download_backup(self, local_path):
        transport = paramiko.Transport((self.device['host'], self.device['port']))
        transport.connect(None, self.device['username'], self.device['password'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = "/" + self.last_backup['name'] + ".backup"

        try:
            sftp.get(remotepath=remote_path, localpath=local_path)
            return True

        except Exception as e:
            if "Permission denied" in str(e):
                print(f"ERROR: Permission denied in local folder {local_path}")
            
            return False

    def download_export(self, local_path):
        export = ""

        for line in str(self.net_connect.send_command("/export terse", delay_factor=8)).splitlines():
            if line != "":
                if export == "":
                    export += line
                else:
                    export += "\n" + line

            else:
                break

        file = open(local_path + f"/export_{self.current_datetime}.rsc", "a")
        file.write(export)
        file.close()

        return f"{local_path}" + f"/export_{self.current_datetime}.rsc"

    def enable_cloud_dns(self):        
        self.net_connect.send_command("/ip cloud set ddns-enabled=yes")
        time.sleep(2)

        return self.net_connect.send_command(":put [/ip cloud get dns-name]")

    def make_backup(self, name="backup", password="", encryption="aes-sha256", dont_encrypt="yes"):
        self.last_backup['name'] = name + "_" + self.get_identity() + "_" + self.current_datetime

        self.output = self.net_connect.send_command(f"/system backup save name={self.last_backup['name']} password={password} encryption={encryption} dont-encrypt={dont_encrypt}")    

        if "backup saved" in self.output:
            return True
        else:
            return False

    def send_command(self, query):
        output = ""

        for line in str(self.net_connect.send_command(query, delay_factor=8)).splitlines():
            if line != "":
                if output == "":
                    output += line
                else:
                    output += "\n" + line
        
        return output