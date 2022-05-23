#!/bin/bash
#set -x
###########################################################################################
# Script to perform full Aruba 7210 wireless controller audit showing for name,mac,ip group and controller affinity for every AP
#
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.2 .200.181.173.202.206.242 = IpAddress: 172.17.32.212
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.3 .200.181.173.202.206.242 = STRING: "MyFirstAP"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.4 .200.181.173.202.206.242 = STRING: "default"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.6 .200.181.173.202.206.242 = STRING: "CND4J0T05X"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.9 .200.181.173.202.206.242 = INTEGER: 2
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.10 .200.181.173.202.206.242 = INTEGER: 4
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.11 .200.181.173.202.206.242 = INTEGER: 2
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.12 .200.181.173.202.206.242 = Timeticks: (317800) 0:52:58.00
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.13 .200.181.173.202.206.242 = STRING: "315"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.33 .200.181.173.202.206.242 = STRING: "A1.0"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.34 .200.181.173.202.206.242 = STRING: "8.3.0.2"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.37 .200.181.173.202.206.242 = IpAddress: 172.17.32.212
#
# Bas Nap Sept 2018
#
###########################################################################################

###########################################################################################
# Global VARS
###########################################################################################
. sitevars
# D=$(date "+%Y%m%d")
# today=$(date -d "today" +"%Y%m%d%H%M%S")
# days=$(date -d "today" +"%Y%m%d")

D="20220429" ### just for test
today="20220429"$(date -d "today" +"%H%M%S")
days="20220429"

times=$(date -d "today" +"%H:%M:%S")

# SNMP OID vars
community_string=42tOCTGZgK4^Q9pl5%QB

serial_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.6"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.6.128.141.183.207.236.0 = STRING: "CNGBK7Y1JB"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.6.128.141.183.207.236.20 = STRING: "CNGBK7Y1JC"

mac_oid="SNMPv2-SMI::enterprises.14823.2.2.1.16.1.1.1.1.2"
#SNMPv2-SMI::enterprises.14823.2.2.1.16.1.1.1.1.2.128.141.183.207.236.0.1 = Hex-STRING: 80 8D B7 CF EC 00
#SNMPv2-SMI::enterprises.14823.2.2.1.16.1.1.1.1.2.128.141.183.207.236.0.2 = Hex-STRING: 80 8D B7 CF EC 01
#SNMPv2-SMI::enterprises.14823.2.2.1.16.1.1.1.1.2.128.141.183.207.236.20.1 = Hex-STRING: 80 8D B7 CF EC 14

name_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.3"
ip_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.2"
group_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.4"
controller_affinity_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.39"

ap_type_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.13"
ap_boot_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.34"
ap_fw_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.33"
ap_uptime_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.12"
channel_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.5.1.15"
ssid_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.7.1.2"

        #operatingmode_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.13.200.181.173.202.206.242"
        #power_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.13.200.181.173.202.206.242"
        #radio_oid="SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.13.200.181.173.202.206.242"

output_dir="/LOG/wireless/${days}/"
[ -d $output_dir ] || mkdir -p $output_dir
output_file="${output_dir}${FILE_PREFIX}APMaster_${today}.csv"

###########################################################################################
# MAIN ROUTINE
###########################################################################################


# it appears that the Mobility Manager can not handle SNMP requests, so have to query the individual controllers
for wlc_team_ip in 172.17.34.92 172.17.34.93
do
echo "Probing WLC controller at $wlc_team_ip"
# Run the snmpwalk command and dump it in files
#for oid in $serial_oid $mac_oid $name_oid $ip_oid $group_oid $controller_affinity_oid $ap_type_oid $ap_boot_oid $ap_fw_oid $ssid_oid $operatingmode_oid $power_oid $channel_oid $radio_oid $ap_uptime_oid
#do
    #echo "Retrieving OID: $oid"
    #snmpwalk -v2c -c $community_string $wlc_team_ip $oid >> /tmp/$$.$oid
#done
done

# print header
#echo "site_id,date,time,ap_name,sn,mac,ip,ap_firmware,group,controller,ap_model,ap_boot,ssid,operatingmode_radio1,operatingmode_radio2,power_radio1,power_radio2,channel_radio1,channel_radio2,state_radio1,state_radio2,ap_uptime" > $output_file

# process the individual files and build an array based of the index from the SN files (if no SN, entity doesn't exist)

 # gawk -F= -v siteid=$SITEID -v days=$days -v times=$times -v ssid_oid=/tmp/$$.$ssid_oid  -v mac_oid=/tmp/$$.$mac_oid -v name_oid=/tmp/$$.$name_oid -v ip_oid=/tmp/$$.$ip_oid -v group_oid=/tmp/$$.$group_oid -v controller_affinity_oid=/tmp/$$.$controller_affinity_oid -v ap_type_oid=/tmp/$$.$ap_type_oid -v ap_boot_oid=/tmp/$$.$ap_boot_oid -v ap_fw_oid=/tmp/$$.$ap_fw_oid -v power_oid=/tmp/$$.$power_oid -v channel_oid=/tmp/$$.$channel_oid -v radio_oid=/tmp/$$.$radio_oid -v operatingmode_oid=/tmp/$$.$operatingmode_oid -v ap_uptime_oid=/tmp/$$.$ap_uptime_oid '

# BEGIN  {
#    # build arrays. The APs are uniquely keyed with some long string:
#        # 128.141.183.207.236.0 or
#        # 200.181.173.202.206.242
#        # As a 1st approximation, for their uniqness I will just take the 2 LSB tuples e.g. 236.0 and 206.242
#        # mac is an exception as the id is shifted to n-2 and n-1. there are 2 entries and we need the .1 thus adding that in in the print


#    file=name_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,mc,"\""); name[id]=mc[2] }
#    file=mac_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-2]" "ind[n-1]" "ind[n];split ($2,mc,":"); gsub (" ",":",mc[2]); mb=substr(mc[2],2,17); mac[id]=mb; }
#        file=ip_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,mc,":");gsub (" ","",mc[2]); ip[id]=mc[2] }
#    file=group_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n];split ($2,mc,"\""); group[id]=mc[2] }
#    file=controller_affinity_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,mc,":"); gsub (" ","",mc[2]); controller[id]=mc[2] }

#        file=ap_type_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,mc,"\""); aptype[id]=mc[2] }
#    file=ap_boot_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,mc,"\""); apboot[id]=mc[2] }
#    file=ap_fw_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n];split ($2,mc,"\""); apfw[id]=mc[2] }

#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.7.1.2. 128.141.183.207.236.20 .1.128.141.183.126.193.80 = STRING: "symbotic-mfg-a"
#SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.7.1.2. 128.141.183.207.236.20 .1.128.141.183.126.193.81 = STRING: "Product_IT_Aruba"

#    file=ssid_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-8]" "ind[n-7]" "; split ($2,mc,":"); gsub ("\"","",mc[2]); gsub (" ","",mc[2]); ssid[id]=mc[2]" "ssid[id] }

#        file=channel_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-2]" "ind[n-1]" "ind[n]; split ($2,mc,":"); gsub ("\"","",mc[2]); chan=int(mc[2]); channel[id]=chan }

#        file=operatingmode_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=int(ind[10]); radio=int(ind[11]); split ($2,mc,":"); val=int(mc[2]); if ( val == 2 ) val="AP/Local mesh"; if (val == 3 ) val="AP only"; operatingmode[id"-"radio]=val}
#        file=power_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=int(ind[10]); radio=int(ind[11]); split ($2,mc,":"); val=int(mc[2]); power[id"-"radio]=val}

#        file=radio_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=int(ind[10]); radio=int(ind[11]); split ($2,mc,":"); val=int(mc[2]); if ( val == 1 ) val="On"; if (val == 2 ) val="Off"; radiostate[id"-"radio]=val}
#        # SNMPv2-SMI::enterprises.14823.2.2.1.5.2.1.4.1.12.200.181.173.202.206.242 = Timeticks: (1044200) 2:54:02.00
#        file=ap_uptime_oid;while ((getline < file )> 0 ) { n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; split ($2,upt," "); uptime[id]=upt[3]" "upt[4]" "upt[5]; gsub(/,/,"",uptime[id]) }
#} # end of BEGIN

## Start of MAIN gawk
#{
        # running the list of all that have a serial number. If you dont have that you dont get listed
        # mac is an exception as the id is shifted to n-2 and n-1. there are 2 entries and we need the .1 thus adding that in in the print
#    n=split ($1,ind,"."); id=ind[n-1]" "ind[n]; altid=ind[n-1]" "ind[n]"1 "
#    split ($2,serial,"\"");sn=serial[2]
#    printf("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",siteid,days,times,name[id],sn,mac[altid],ip[id],apfw[id],group[id],controller[id],aptype[id],apboot[id],ssid[id],"opmode1","opmode2","power","power2",channel[altid],"ch2","rstate1","rstate2",uptime[id])

#}' < /tmp/$$.$serial_oid | sort | uniq >> $output_file

# Keep a local copy in /LOG/wireless as a general inventory
#cp $output_file /LOG/wireless/get_aruba_wlc_inventory.csv
# cp $output_file /LOG/wireless/get_wlc_inventory.csv
# cat $output_file

## cleanup
#rm /tmp/$$.*

