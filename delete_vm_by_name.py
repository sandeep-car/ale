#!/usr/local/bin/python3.7
#
# DISCLAIMER: This script is not supported by Nutanix. Please contact
# Sandeep Cariapa (sandeep.cariapa@nutanix.com) if you have any questions.
# Last updated: 9/29/2018
# This script uses Python 3.7.
# NOTE:
# 1. You need a Python library called "requests" which is available from
# the url: http://docs.python-requests.org/en/latest/user/install/#install
# For reference look at:
# https://github.com/nutanix/Connection-viaREST/blob/master/nutanix-rest-api-v2-script.py
# https://github.com/nelsonad77/acropolis-api-examples

import sys
import json
import requests
import clusterconfig as C
from pprint import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Print usage messages.
def PrintUsage():

    print ("<Usage>:",sys.argv[0],"<VM Name>")
    print ("Where <VM Name is the name of the VM to be deleted.")
    print ("If there are multiple VMs with the same name we will delete one of them randonly :-)")
    return

# Delete a VM with the given UUID.
def deletevm(mycluster,vmid):

    cluster_url = mycluster.base_urlv2 + "vms/" + vmid
    print("Deleting VM",cluster_url)
    try:
        server_response = mycluster.sessionv2.delete(cluster_url)
        return server_response.status_code ,json.loads(server_response.text)
    except Exception as ex:
        print(ex)
        return -1,cluster_url

if __name__ == "__main__":
    try:
        if (len(sys.argv) != 2):
            PrintUsage()
            sys.exit(1)
        
        vm_name = sys.argv[1]
        
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        mycluster = C.my_api(C.cluster_ip,C.cluster_admin,C.cluster_pwd)
        status, cluster = mycluster.get_cluster_information()
        if (status != 200):
            print ("Cannot connect to ",cluster)
            print ("Did you remember to update the config file?")
            sys.exit(1)

        # Get information about all VMs in the cluster.
        status,all_vms = mycluster.get_all_vm_info()
        all_vms_list = all_vms["entities"]
        # pprint(all_vms_list)
        for vm_dict in all_vms_list:
            # If you were looking for a VM with a particular UUID, you would be matching for it here.
            if (vm_name == vm_dict["name"]):
                vm_uuid = vm_dict["uuid"]
                break
        try:
            print ("UUID of your VM is:",vm_uuid)
        except NameError:
            print (">>> Cannot proceed because we cannot find",vm_name)
            sys.exit(1)

        status, resp = deletevm(mycluster,vm_uuid)
        if (status != 201):
            print ("Could not delete:",vm_name)
            sys.exit(1)
        else:
            print ("Successfully deleted:",vm_name)

    except Exception as ex:
        print(ex)
        sys.exit(1)
