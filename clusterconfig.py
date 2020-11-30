# DISCLAIMER: This script is not supported by Nutanix. Please contact
# Sandeep Cariapa (lastname@gmail.com) if you have any questions.
import json
import uuid
import requests
from pprint import pprint
from urllib.parse import quote

# Cluster credentials.
cluster_ip = "10.21.101.37"
cluster_admin = "restapiuser"
cluster_pwd = "blah blah"

# Golden VMs. These are the VMs that are members of each student POD.
# These could be read in from a CSV file provided as an argument also.
ALE_VMS = [ "sample_vm1", "sample_vm2"]


# ========== DO NOT CHANGE ANYTHING UNDER THIS LINE =====
class my_api():
    def __init__(self,ip,username,password):
        
        # Cluster IP, username, password.
        self.ip_addr = ip
        self.username = username
        self.password = password
        # Base URL at which v0.8 REST services are hosted in Prism Gateway.
        base_urlv08 = 'https://%s:9440/PrismGateway/services/rest/v0.8/'
        self.base_urlv08 = base_urlv08 % self.ip_addr
        self.sessionv08 = self.get_server_session(self.username, self.password)
        # Base URL at which v1 REST services are hosted in Prism Gateway.
        base_urlv1 = 'https://%s:9440/PrismGateway/services/rest/v1/'
        self.base_urlv1 = base_urlv1 % self.ip_addr
        self.sessionv1 = self.get_server_session(self.username, self.password)
        # Base URL at which v2 REST services are hosted in Prism Gateway.
        base_urlv2 = 'https://%s:9440/PrismGateway/services/rest/v2.0/'
        self.base_urlv2 = base_urlv2 % self.ip_addr
        self.sessionv2 = self.get_server_session(self.username, self.password)
        # Base URL at which v2 REST services are hosted in Prism Gateway.
        base_urlv3 = 'https://%s:9440/PrismGateway/services/rest/v3.0/'
        self.base_urlv3 = base_urlv3 % self.ip_addr
        self.sessionv3 = self.get_server_session(self.username, self.password)
        
    def get_server_session(self, username, password):

        # Creating REST client session for server connection, after globally
        # setting authorization, content type, and character set.
        session = requests.Session()
        session.auth = (username, password)
        session.verify = False
        session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
        return session

    # Get cluster information.
    def get_cluster_information(self):

        cluster_url = self.base_urlv2 + "cluster/"
        print("Getting cluster information for cluster", self.ip_addr)
        try:
            server_response = self.sessionv2.get(cluster_url)
            return server_response.status_code ,json.loads(server_response.text)
        except Exception as ex:
            print(ex)
            return -1,cluster_url

    # Get list of all VMs.
    def get_all_vm_info(self):

        cluster_url = self.base_urlv2 + \
                      "vms/?include_vm_disk_config=true&include_vm_nic_config=true"
        server_response = self.sessionv2.get(cluster_url)
        # print("Response code: ",server_response.status_code)
        return server_response.status_code, json.loads(server_response.text)

    # Clone a VM with the given UUID
    def clonevm(self,vmid,vm_name,network_uuid):

        # If the cloned VM was to have > 1 NIC, you would send over a list of network UUIDs.
        # And loop through that here to fill out vm_nics[]
        vm_nic={}
        vm_nic["network_uuid"] = network_uuid
        vm_nics=[]
        vm_nics.append(vm_nic)

        print("VM_NICS: ", type(vm_nics))
        pprint(vm_nics)

        # Setting override_network_config to True here means it takes the network info we give it (vm_nics etc)
        # instead of cloning it from the source VM.
        vm_clone_proto = {
            "override_network_config": True,
            "name": vm_name,
            "uuid": str(uuid.uuid4()),
            "vm_nics": vm_nics,
        }

        print("VM_CLONE_PROTO: ", type(vm_clone_proto))
        pprint(vm_clone_proto)

        specs = []
        specs.append(vm_clone_proto)
        
        vm_clone_spec = {}
        vm_clone_spec["spec_list"] = specs
        
        cloneuuid =  vm_clone_spec['spec_list'][0]["uuid"]
        print("Cloneuuid:",cloneuuid)
        cluster_url = self.base_urlv2 + "vms/" + str(quote(vmid)) + "/clone"
        print("Cloning VM",cluster_url)
        try:
            server_response = self.sessionv2.post(cluster_url, data=json.dumps(vm_clone_spec))
            return server_response.status_code, cloneuuid, json.loads(server_response.text)
        except Exception as ex:
            print(ex)
            return -1,0,cluster_url
            
    # Power on VM with this UUID.
    def power_on_vm(self, vmid):

        print("Powering on VM: %s." % vmid)
        cluster_url = self.base_urlv2 + "vms/" + str(quote(vmid)) + "/set_power_state/"
        vm_power_post = {"transition":"ON"}
        server_response = self.sessionv2.post(cluster_url, data=json.dumps(vm_power_post))
        print("Response code: %s" % server_response.status_code)
        return server_response.status_code ,json.loads(server_response.text)

    # Just hang out until the task is complete.
    def poll_task(self, task_uuid):

        cluster_url = self.base_urlv2 + "tasks/poll/"
        vm_poll_post = {"completed_tasks": [task_uuid]}
        print("Polling task %s. Cluster_URL %s" % (task_uuid,cluster_url))
        # Loop until status is succeeded.
        while True:
            server_response = self.sessionv2.post(cluster_url, data=json.dumps(vm_poll_post))
            r = json.loads(server_response.text)
            ps = str(r["completed_tasks_info"][0]["progress_status"])
            if ps == "Succeeded":
                break
                # End while loop
        return

    # Get network info. Called by get_usable_vlans() below.
    def get_network_info(self):
        
        cluster_url = self.base_urlv2 + "/networks/"
        print("Getting network info")
        server_response = self.sessionv2.get(cluster_url)
        print("Response code: %s" % server_response.status_code)
        return server_response.status_code ,json.loads(server_response.text)
        
    # Return num usable VLANs.
    def get_usable_vlans(self,num):

        status,resp = self.get_network_info()
        all_networks = resp["entities"]
        
        used_vlans = []
        for network in all_networks:
            used_vlans.append(network["vlan_id"])

        # print("Used VLANS")
        # pprint(used_vlans)

        # Uncomment in production. All VLANs range from 0 to 4095.
        # all_vlans = list(set(range(4096)))
        all_vlans = [1102, 1103, 1104]
        # print("All VLANS")
        # pprint(all_vlans)

        usable_vlans = list(set(all_vlans) - set(used_vlans))
        usable_vlans.sort()
        # print("Usable VLANs", len(usable_vlans))
        # pprint(usable_vlans)
        ret_vlans = usable_vlans[0:num]

        return ret_vlans

    # Create a network.
    def create_network(self,vlan,prefix):

        network_spec = {
            "vlan_id": str(vlan),
            "name": prefix + "_student." + str(vlan),
            "annotation": "student." + str(vlan)
        }

        cluster_url = self.base_urlv2 + "networks/"
        print("Creating network", cluster_url)
        try:
            server_response = self.sessionv2.post(cluster_url, data=json.dumps(network_spec))
            return server_response.status_code,json.loads(server_response.text)
        except Exception as ex:
            print(ex)
            return -1,cluster_url

    # Update VM with network uuid.
    def update_vm_network(self,vmid,network_uuid):
        
        vm_update_spec = {
            "vm_nics": [
                { "network_uuid": network_uuid }
            ]
        }

        cluster_url = self.base_urlv2 + "vms/" + str(quote(vmid))
        print("Updating VM",cluster_url)
        try:
            server_response = self.sessionv2.put(cluster_url, data=json.dumps(vm_update_spec))
            return server_response.status_code, json.loads(server_response.text)
        except Exception as ex:
            print(ex)
            return -1,cluster_url
