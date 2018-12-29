# ale
HOWTO.txt describes the process required to configure a Deployment VM. Run scripts from this Deployment VM.

Please be sure to update variables in clusterconfig.py also.

Run ale_create_vlan.py with an argument corresponding to the number of student PODs. 
Each student POD will have clones of the VMs in ALE_VMS, which is specified in clusterconfig.py. Change ALE_VMS so it has the names of the VMs to be cloned. VMs that are the clone source (i.e. members of ALE_VMS) can have static IPs. Cloned VMs can have the same IP, since they will be in different VLANs.

all_vlans in clusterconfig.get_usable_vlans() is a list of VLANs that each student POD will be in. You cannot have more students than there are available VLANs. You can either update this variable to the list of available VLANs, or uncomment 

\# all_vlans = list(set(range(4096)))
to include all available VLANs.
Note that you will need to modify the TOR switch so it routes the VLANs in all_vlans.

If you don't want to modify the TOR switch, you can ensure that each student POD runs on a particular host by using host affinity.
