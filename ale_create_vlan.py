#!/usr/local/bin/python3.7
#
# DISCLAIMER: This script is not supported by Nutanix. Please contact
# Sandeep Cariapa (lastname@gmail.com) if you have any questions.
# NOTE:
# Please read the HOWTO and README files included with this distribution before proceeding.
# For reference look at:
# https://github.com/sandeep-car/api-lab
# https://github.com/nutanix/Connection-viaREST/blob/master/nutanix-rest-api-v2-script.py
import sys
import json
import uuid
import requests
import argparse
import clusterconfig as C
from pprint import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Sample_vm2 has an attached ISO of Fedora Core.
student_pod = C.ALE_VMS

# Network name prefix.
network_name_prefix = "ale"

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("num_students", type=int, help="Number of student pods.")
        args = parser.parse_args()
        
        num_students = args.num_students
        
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        mycluster = C.my_api(C.cluster_ip, C.cluster_admin, C.cluster_pwd)
        status, cluster = mycluster.get_cluster_information()
        if status != 200:
            print("Cannot connect to: %s" % cluster)
            print(">>> Did you remember to update the config file? <<<")
            sys.exit(1)
        
        # Get specific cluster elements.
        print("Name: %s." % cluster["name"])
        print("ID: %s." % cluster["id"])
        print("Cluster Ext IP Address: %s." % cluster["cluster_external_ipaddress"])
        print("Number of Nodes: %s." % cluster["num_nodes"])
        print("Version: %s." % cluster["version"])

        # Get VM info so we can grab UUIDs of VMs we need to clone.
        status, all_vms = mycluster.get_all_vm_info()
        all_vms_list = all_vms["entities"]
        # pprint(all_vms_list)

        # Get list of available VLANs.
        vlan_list = mycluster.get_usable_vlans(num_students)
        print("Usable vlans:")
        pprint(vlan_list)
        if len(vlan_list) < num_students:
            print ("Sorry dude, you've run out of VLANs. Free some up, or choose a fewer number of students.")
            sys.exit(1)

        networks_byvlan = {}
        # Create network/VLANs, one for each student.
        for vlan in vlan_list:
            print ("Creating Vlan: ", vlan)

            status, resp = mycluster.create_network(vlan,network_name_prefix)
            print("Status, Resp", status, resp)
            if status != 201:
                print("Could not create VLAN:",vlan,status)
                pprint(resp)
                sys.exit(1)
            
            networks_byvlan[vlan] = resp["network_uuid"]

        # Create student PODs.
        # Outer loop is for VLANs, because each POD must be within its own VLAN.
        for vlan,network_uuid in networks_byvlan.items():
            for clone_source in student_pod:
                print ("Clone_Source: ", clone_source)
                
                for vm_dict in all_vms_list:
                    if vm_dict["name"] != clone_source:
                        continue
                    # If vm_dict["name"] matches the clone_source.
                    vm_name = clone_source + "." + str(vlan)
                    vm_uuid = vm_dict["uuid"]
                    status, cloneuuid, resp = mycluster.clonevm(vm_uuid,vm_name,network_uuid)
                    print("Status, CloneUUID, Resp", status, cloneuuid, resp)
                    if status != 201:
                        print ("Could not clone:",vm_name,status)
                        pprint(resp)
                        sys.exit(1)
                    
                    # Poll the task UUID until complete.
                    taskid = resp["task_uuid"]
                    mycluster.poll_task(taskid)
                    
                    # Power on the cloned VM.
                    status,resp = mycluster.power_on_vm(cloneuuid)
                # End for vm_dict.
            # End for clone_source.
        # End for vlan.
                        
        
        print("=")
        print("*COMPLETE*")

    except Exception as ex:
        print(ex)
        sys.exit(1)
