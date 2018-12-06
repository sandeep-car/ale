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
from urllib.parse import quote
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Print usage messages.
def PrintUsage():

    print ("<Usage>:",sys.argv[0],"<Network Name>")
    print ("Where <Network Name is the name of the Network to be deleted.")
    print ("If there are multiple Networks with the same name we will delete one of them randonly :-)")
    return

# Delete a Network with the given UUID.
def deletenetwork(mycluster,networkid):

    cluster_url = mycluster.base_urlv2 + "networks/" + str(quote(networkid))
    print("Deleting Network",cluster_url)
    try:
        server_response = mycluster.sessionv2.delete(cluster_url)
        return server_response.status_code
    except Exception as ex:
        print("Exception: ", ex)
        return -1,cluster_url

if __name__ == "__main__":
    try:
        if (len(sys.argv) != 2):
            PrintUsage()
            sys.exit(1)
        
        network_name = sys.argv[1]
        
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        mycluster = C.my_api(C.cluster_ip,C.cluster_admin,C.cluster_pwd)
        status, cluster = mycluster.get_cluster_information()
        if (status != 200):
            print ("Cannot connect to ",cluster)
            print ("Did you remember to update the config file?")
            sys.exit(1)

        # Get information about all Networks in the cluster.
        status,all_networks = mycluster.get_network_info()
        all_networks_list = all_networks["entities"]
        # pprint(all_networks_list)
        for network in all_networks_list:
            # If you were looking for a Network with a particular UUID, you would be matching for it here.
            if (network_name == network["name"]):
                network_uuid = network["uuid"]
                break
        try:
            print ("UUID of your Network is:",network_uuid)
        except NameError:
            print (">>> Cannot proceed because we cannot find",network_name)
            sys.exit(1)

        status = deletenetwork(mycluster,network_uuid)
        print("Status: ", status)
        if (status != 204):
            print ("Could not delete:",network_name)
            sys.exit(1)
        else:
            print ("Successfully deleted:",network_name)

    except Exception as ex:
        print(ex)
        sys.exit(1)
