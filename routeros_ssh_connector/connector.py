import re
import time

from netmiko import Netmiko

class MikrotikDevice:
    def __init__(self):
        pass


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
    def update_identity(self, name):
        return self.check_addset_result(self.net_connect.send_command(f"/system identity set name={name}"))

    def update_services(self, service, disabled, port=None, address=None):
        self.command = f"/ip service set {service} disabled={disabled}"

        if port != None:
            self.command += f" port={port}"
        
        if address != None:
            self.command += f" address={address}"

        return self.check_addset_result(self.net_connect.send_command(self.command))

    def update_user(self, username, password, group):
        self.command = f"/user set {username}"        

        if password != "":
            self.command += f" password={password}"

        if group != "":
            self.command += f" group={group}"

        return self.check_addset_result(self.net_connect.send_command(self.command))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def create_ip_address(self, ip_address, interface):
        return self.check_addset_result(self.net_connect.send_command(f"/ip address add address={ip_address} interface={interface}"))

    def create_route(self, dst_address, gateway, distance, disabled):
        return self.check_addset_result(self.net_connect.send_command(f"/ip route add dst-address={dst_address} gateway={gateway} distance={distance} disabled={disabled}"))

    def create_user(self, username, password, group):
        return self.check_addset_result(self.net_connect.send_command(f"/user add name={username} password={password} group={group}"))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def check_addset_result(self, command_output):
        for line in command_output.splitlines():
            parsed = re.sub(" +", " ", line).strip()

            if parsed != "":
                return parsed
            else:
                return True


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def do_backup(self, dont_encrypt):
        self.output = self.net_connect.send_command(f"/system backup save dont-encrypt={dont_encrypt}")    

        if "backup saved" in self.output:
            return True
        else:
            return False

    def enable_cloud_dns(self):        
        self.net_connect.send_command("/ip cloud set ddns-enabled=yes")
        time.sleep(2)

        return self.net_connect.send_command(":put [/ip cloud get dns-name]")

    def export_configuration(self):
        self.output = self.net_connect.send_command("/export terse", delay_factor=8)    

        output = ""    

        for line in self.output.splitlines():
            output += "\n" + line
        
        return output

    def send_command(self, query):
        output = ""

        for line in str(self.net_connect.send_command(query)).splitlines():
            if line != "":
                if output == "":
                    output += line
                else:
                    output += "\n" + line
        
        return output