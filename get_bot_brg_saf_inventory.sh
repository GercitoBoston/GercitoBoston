#!/bin/bash
#set -x
#THIS_SCRIPT_VERSION="0.7.7" #a big mac has 26 grams of fat

# this script exists because Joe Walker made it exist.
#
# What it does:
# Connects to DNS server, determines which interface is for the bot vlan (172.17.16.0/20)
# Read /var/log/messages (future: all messages sorted for the past 5 days) and extracts anything that has a DHCPACK
# with this list (vlanFile)
# Obtains the BotAutoStartup file for simba bot version assignments.
# Queries all bridges for their firmware level.
# with all known details, generates a CSV file with all bot/bridge/safety details & versions
# format is:
#    site_id,date,time,botID,mfgr,simba_version,brg_firmware,brg_ip,brg_mac,bot_ip,bot_mac,saf_ip,saf_mac,status

# merge SNMP loops to 1 loop
######################################################################
# Standard opening BEGINS
######################################################################
. sitevars
#declare -r PARENT_COMMAND=$(ps -o args= $PPID)
#declare -r THIS_SCRIPT=$(basename $0)

#while getopts "v" argOption
#do
#	case ${argOption} in
#		v)
#			echo "${THIS_SCRIPT} VERSION: ${THIS_SCRIPT_VERSION}"
#			exit 0
#		;;
#	esac
#done

## printf "20220429"$(date -d "today" +"%H%M%S")" ${THIS_SCRIPT} called by ${PARENT_COMMAND}\n" | tee -a /home/jwalker/${THIS_SCRIPT}.log
#declare -i pid_death_counter
#declare -ir PID_DEATH_RETRIES=120
#declare -ir PID_DEATH_RETRY_DELAY=30
#declare -r PID_FILE="/var/run/${THIS_SCRIPT}.pid"
# trap 'if [ $(cat ${PID_FILE}) -eq $$ ]; then rm -f ${PID_FILE}; fi;' EXIT # only kill my pid
# trap 'echo "$0 is terminating ..."; exit 3' 15
# while [ -e ${PID_FILE} ]
# do
# 	#loop a few times every minute and retry, or abort after x
# 	((pid_death_counter++))
# 	printf "$(date "+%Y-%m-%d %H:%M:%S %Z") PID file exists, "
# 	ps h -p $(cat ${PID_FILE}) 1>&2 > /dev/null
# 	if [ $? -eq 1 ]
# 	then
# 		printf "and no running process is associated to it, "
# 	fi
# 	if [ ${pid_death_counter} -lt ${PID_DEATH_RETRIES} ]
# 	then
# 		printf "waiting to retry at $(date -d "+${PID_DEATH_RETRY_DELAY} seconds" "+%Y-%m-%d %H:%M:%S")\n"
# 		sleep ${PID_DEATH_RETRY_DELAY}
# 	else
# 		printf "and the number of retries allowed has been reached but the PID file \"${PID_FILE}\" still exists.  Exiting\n"
# 		printf "###############################################################\n"
# 		printf "$(date "+%Y-%m-%d %H:%M:%S %Z") $(basename $0) has finished running...\n"
# 		printf "###############################################################\n"
# 		exit 1 # aint no sunshine till the pid is gone
# 	fi
# done
# echo $$ > ${PID_FILE} || exit 1 # cant write pid file.
######################################################################
# Standard opening ENDS
######################################################################


# Create my vars
declare -r DATE_STAMP="$(date +%Y%m%d)"
declare -r YESTERDAY="$(date --date="Yesterday" +%Y%m%d)"
declare -r TIME_STAMP=$(date +%H:%M:%S)
#declare dateTimeStamp=$(date "+%Y%m%dT%H%M%S")
logDir="/LOG/wireless"
declare -r outputDir="${logDir}/${DATE_STAMP}"
[ -d ${outputDir} ] || mkdir -p ${outputDir}
declare -r sshKey="/root/.ssh/id_rsa_icinga"
if [ $(hostname -f) = "555monitor01.itsvc.tgt-555.symbotic" ]
then
	declare -r userDNS="root@172.17.34.12"
	declare -r userSyssupport="root@555botsup01v.mbot.tgt-555.symbotic"
else
	declare -r userDNS="root@172.17.34.10"
	declare -r userSyssupport="root@syssupport.services.symbotic"
fi
declare -r strictHostKeyChecking="no"
declare -r outFile="${outputDir}/${FILE_PREFIX}BotMaster_$(date +%Y%m%d%H%M%S).csv"
declare snmpFile="${logDir}/${THIS_SCRIPT}_snmp_results.${DATE_STAMP}.csv"
declare oldSnmpFile="${logDir}/${THIS_SCRIPT}_snmp_results.${YESTERDAY}.csv"
declare -r vlanFile="${logDir}/vlan16.devices.csv"
declare -r simbaFile="${logDir}/BotAutoStartup.txt"
#declare snmpScript="${outputDir}/queryBridges.sh"
declare -r currentFile="${logDir}/get_bot_brg_saf_inventory.csv"
declare -r siteName=${SITEID}
declare -r querySleepSeconds="0.1"
declare -ri dhcpLookbackDays="5"
declare -r tmpDirRemote="/tmp"
declare -r botAutoStartupFile="/export/Engineering/Simba/BotAutoStartup.txt"
declare doNotCompare="false"
#where the scripts live
declare -r cdsDir="/etc/icinga2/scripts/"
#how far back in seconds to search messages for devices
# 5 days = 432000
declare -ri goBackSeconds=432000
declare -ir LINES_HEAD=3
declare -ir LINES_TAIL=2


find /LOG/wireless -maxdepth 1 -type f -name "get_bot_brg_saf_inventory_snmp_results*.csv" -mtime +1 -delete

# create list of all ACK devices in vlan
echo "$(date "+%Y-%m-%d %H:%M:%S %Z") determining NIC"
## activeNIC=$(ssh -o StrictHostKeyChecking=${strictHostKeyChecking} -i ${sshKey} ${userDNS} ip a | grep '172.17.16' -B2 | head -n 1 | gawk '{ truncStop=length($2)-1; print substr($2,1,truncStop) }' | gawk -F@ '{ print $1 }')
#echo "activeNIC: ${activeNIC}"
#handle the output variations at sites
#+ activeNIC=eth6
#+ activeNIC=ens160.16@ens160
#activeNIC=$(echo ${activeNIC} | gawk -F@ '{ print $1 }')

# match parens on next line so NPP isn't a little bastard about it:  tr -d '('
echo "$(date "+%Y-%m-%d %H:%M:%S %Z") pulling recent and revelant leases."
# ssh -o StrictHostKeyChecking=${strictHostKeyChecking} -i ${sshKey} ${userDNS} "find /var/log -maxdepth 1 -name messages* -mtime -${dhcpLookbackDays} | xargs -I {} cat {}" | gawk -v goBackSeconds=${goBackSeconds} -v year=$(date +"%Y") 'BEGIN {
# 	#-v goBackSeconds
# 	#-v year
# 	nowDDT=systime()
# 	seekTime=nowDDT-goBackSeconds
# }

# {
# 	day=$2
# 	split($3,timeArr,":")
# 	hr=timeArr[1]
# 	min=timeArr[2]
# 	sec=timeArr[3]

# 	if ($1 ~ /Jan/) { month=01 }
# 	if ($1 ~ /Feb/) { month=02 }
# 	if ($1 ~ /Mar/) { month=03 }
# 	if ($1 ~ /Apr/) { month=04 }
# 	if ($1 ~ /May/) { month=05 }
# 	if ($1 ~ /Jun/) { month=06 }
# 	if ($1 ~ /Jul/) { month=07 }
# 	if ($1 ~ /Aug/) { month=08 }
# 	if ($1 ~ /Sep/) { month=09 }
# 	if ($1 ~ /Oct/) { month=10 }
# 	if ($1 ~ /Nov/) { month=11 }
# 	if ($1 ~ /Dec/) { month=12 }

# 	dateVar=mktime(year" "month" "day" "hr" "min" "sec)
# 	if (dateVar >= seekTime) {
# 			printf strftime("%F %T -",dateVar) " "
# 			for (i=4; i<=NF; i++) {
# 					printf $i " "
# 			}
# 			printf "\n"
# 	}
# }
# ' | sort -n | grep "${activeNIC}\\s\$" | grep DHCPACK | gawk '
# 	{
# 		if (NF == 12) print $8","$10",NONAME";
# 		if (NF==13) {
# 			print $8","$10","substr($11,2,8)
# 		}
# 	}' | tr -d ')' | sort -u > ${vlanFile}

#vlanFile format:
#172.17.16.171,00:1e:c0:89:ad:88,saf02425
#172.17.16.172,00:04:a3:da:12:e2,bot2425
#172.17.16.176,88:51:fb:77:60:8f,brg02421


# get simba firmware assignments
echo "$(date "+%Y-%m-%d %H:%M:%S %Z") getting BotAutoStartup.txt file"
printf "get ${botAutoStartupFile} ${simbaFile}.tmp\nbye\n" | sftp -b - -i ${ID_RSA} ${userSyssupport} 2>&1 > /dev/null
if [ -s ${simbaFile}.tmp ]
then
	mv ${simbaFile}.tmp ${simbaFile}
else
	if [ -s ${simbaFile} ]
	then
		echo "$(date "+%Y-%m-%d %H:%M:%S %Z") WARNING BotAutoStartup.txt file was not refreshed.  Results may not be accurate"
	else
		echo "$(date "+%Y-%m-%d %H:%M:%S %Z") FAIL BotAutoStartup.txt could not be downloaded and no previous copy was found."
	fi
fi

printf "$(date "+%Y-%m-%d %H:%M:%S %Z") collecting bridge firmware details." #no newline b/c wait dots
> ${snmpFile}
interval_seconds=10
interval_next=$(date -d "now +${interval_seconds} seconds" +"%s")
echo $'\n'
#for queryData in $(sort -u ${vlanFile} | grep -v -E 'bot|saf') # | gawk -F, '{ print $1 }')
#do
#	current_time=$(date +"%s")
#	#RFC1155-SMI::enterprises.8691.15.29.1.1.5.0 = STRING: "1.11.8 Build 17042115" <<< extract version from this reply
#	#RFC1213-MIB::mib-2.47.1.1.1.1.9.1 = STRING: "V2.0.0.0-eng01-B0012"
#	# stderr outputs:
#	#Timeout: No Response from 192.168.11.29.
#	#RFC1155-SMI::enterprises.8691.15.29.1.1.5.0 = No Such Object available on this agent at this OID
#	queryID=$(echo ${queryData} | gawk -F, '{ print $3 }')
#	echo ${queryData} $'\n'
#	#brg0nnnn becomes nnnn, otherwise 0
#	if [ ${queryID:0:4} = "brg0" ]
#	then
#		queryIP=$(echo ${queryData} | gawk -F, '{ print $1 }')
#		queryMAC=$(echo ${queryData} | gawk -F, '{ print $2 }')
#		queryID=${queryID:4:4}
#		if [ "${queryMAC:0:8}" = '00:90:e8' ] # MOXA JUST WORKS!
#		then
#			queryAnswer=$(snmpget -v 2c -c public ${queryIP} SNMPv2-SMI::enterprises.8691.15.29.1.1.5.0 2> /dev/null | grep STRING gawk -F\" '{ printf $(NF-1) }' )
#		elif [ "${queryMAC:0:8}" = '88:51:fb' ] # HP
#		then
#			queryAnswer=$(snmpget -v 2c -c public ${queryIP} SNMPv2-SMI::mib-2.47.1.1.1.1.9.1 2> /dev/null | grep STRING | gawk -F\" '{ printf $(NF-1) }' )
#		fi
#		#if there is an answer, print it, otherwise unknown
#		#echo "DEBUG: ${queryData} ${queryAnswer}"
#		if [ -z ${queryID} ]
#		then
#			queryID="####"
#		fi
#		if [ -n "${queryAnswer}" ]
#		then
#			queryTime=$(date "+%Y-%m-%d %H:%M:%S %Z")
#			echo "${queryTime},${queryIP},${queryAnswer:-NOVALUE},${queryMAC},${queryID}" >> ${snmpFile}
#			sleep ${querySleepSeconds}
#			if [ ${current_time} -gt ${interval_next} ]
#			then
#				printf "."
#				interval_next=$((interval_next + interval_seconds))
#			fi
#		fi
#	fi
#	unset queryIP
#	unset queryMAC
#	unset queryID
#	unset queryTime
#	unset queryAnswer
#done
unset queryData


printf "\n$(date "+%Y-%m-%d %H:%M:%S %Z") collected bridge firmware details.\n"
#file built format (CSV):
#2018-04-25 14:17:47 EDT,172.17.18.159,1.11.8 Build 17042115
#2018-04-25 14:17:54 EDT,172.17.16.163,V2.0.0.0-eng01-B0012

#find ${logDir}/${YESTERDAY} -maxdepth 1 -name "${FILE_PREFIX}BotMaster_??????????????.csv.gz" -type f -printf "%T@ %p\n" | sort -n | gawk '{ print $2 }' | tail -n 1 | xargs -I {} gunzip --stdout {} > ${logDir}/${YESTERDAY}/${FILE_PREFIX}BotMaster_00000000000000.csv
#yesterFile=$(find ${logDir}/${YESTERDAY} -maxdepth 1 -name "get_bot_brg_saf_inventory_snmp_results.csv")

#if [ ! -r ${oldSnmpFile} ]
#then
#	echo "$(date "+%Y-%m-%d %H:%M:%S %Z") WARNING: Cannot find SNMP results for yesterday, offline assets will not have data." >&2
#	doNotCompare="true"
#	oldSnmpFile=${snmpFile}
#fi


#backfill for anything found in MESSAGES (do not rely on yesterday, use a master file and update it)
#if [ "${doNotCompare}" = "false" ]
#then
#	#extract just the bot #s.  Compare
#	#cat ${oldSnmpFile} | cut -d, -f5 | sort -un > /tmp/${THIS_SCRIPT}_yesterday_bots.list
#	cutoff_time=$(date -d "${dhcpLookbackDays} days ago" +"%s")
#	> /tmp/${THIS_SCRIPT}_yesterday_bots.list
#	sort -n ${oldSnmpFile} | while read line_data
#	do
#		line_time=$(date -d "$(echo ${line_data} | cut -d, -f1)" +%s)
#		# echo "if [ ${cutoff_time} -gt ${line_time} ]"
#		if [ ${line_time} -gt ${cutoff_time} ]
#		then
#			#echo "INCLUDING: ${line_data}"
#			echo ${line_data} >> /tmp/${THIS_SCRIPT}_yesterday_bots.list
#		fi
#	done
#	cat /tmp/${THIS_SCRIPT}_yesterday_bots.list | cut -d, -f5 | sort -n | uniq > /tmp/${THIS_SCRIPT}_yesterday_bots.list.tmp
#	cp /tmp/${THIS_SCRIPT}_yesterday_bots.list.tmp /tmp/${THIS_SCRIPT}_yesterday_bots.list
#	cat ${snmpFile} | cut -d, -f5 | sort -n | uniq > /tmp/${THIS_SCRIPT}_current_bots.list
#	comm -23 /tmp/${THIS_SCRIPT}_yesterday_bots.list /tmp/${THIS_SCRIPT}_current_bots.list > /tmp/${THIS_SCRIPT}_missing_bots.list
#	#must restrict to the single most recent match from previous inventory
#	for miaBotID in $(cat /tmp/${THIS_SCRIPT}_missing_bots.list)
#	do
#		grep ${miaBotID} ${oldSnmpFile} | sort -n | tail -n 1 | gawk -F, '{ print $1","$2","$3","$4","$5 }' >> ${snmpFile}
#	done
#	rm -f /tmp/${THIS_SCRIPT}_missing_bots.list
#fi


#*****grep -o bot....$
#cat ${vlanFile} | grep -o bot.... | gawk -F, \
#	-v vlanFile=${vlanFile} \
#	-v simbaFile=${simbaFile} \
#	-v outFile=${outFile} \
#	-v snmpFile=${snmpFile} \
#	-v siteName=${siteName^^} \
#	-v DATE_STAMP=${DATE_STAMP} \
#	-v TIME_STAMP=${TIME_STAMP} \
#	-v oldSnmpFile=${oldSnmpFile:-/dev/null} \
#'
#BEGIN {
## array field names (and positions)
#bot=1
#brgFW=2
#simba=3
#brgIP=4
#brgMAC=5
#botIP=6
#botMAC=7
#safIP=8
#safMAC=9
#status=10
#brgMfgr=11
#
## make header and a new file all at the same time.
#printf "site_id,date,time,botID,mfgr,simba_version,brg_firmware,brg_ip,brg_mac,bot_ip,bot_mac,saf_ip,saf_mac,status\n" > outFile
#
##END OF BEGIN
#}
#
##MAIN BEGIN
#{
#	# extract just the device number (2273) for later relationships, already filtered just botNNNN
#	#<ip-address>,<mac-address>,<hostname>
#	devNum=substr($0,4,7)
#	botData[devNum][bot]=$0
#	botData[devNum][status]="cached"
##MAIN END
#}
#
#END {
#	#walk the oldSnmpFile and fill in any valid values found with yesterday data
#	while ((getline yesterLine < oldSnmpFile) > 0) {
#		n=split(yesterLine,yesterValues,",")
#		yesterFirmware=yesterValues[3]
#		yesterBrgMAC=yesterValues[4]
#		yesterBotID=yesterValues[5]
#		#printf "DEBUG-YESTER: "yesterFirmware","yesterBrgMAC","yesterBotID"\n"
#		if (botData[yesterBotID][status]) {
#			#printf botData[yesterBotID][status]"\n"
#			botData[yesterBotID][status]="cached"
#			botData[yesterBotID][brgFW]=yesterFirmware
#			botData[yesterBotID][brgMAC]=yesterBrgMAC
#			#botData[yesterBotID][brgIP]="0.0.0.0"
#		}
#	}
#
#	# read the vlanFile and pull all bridge, safety, and bot IP and MAC addresses.  Store in array
#	#<ip-address>,<mac-address>,<hostname>
#	while ((getline devInfo < vlanFile) > 0) {
#		n=split(devInfo,devArr,",")
#		if (n != 0) {
#			devType=substr(devArr[3],1,3)
#			#brg, saf, bot
#			if (devType == "brg") {
#				devNum=(substr(devArr[3],5,8))
#				botData[devNum][brgIP]=devArr[1]
#				botData[devNum][brgMAC]=tolower(devArr[2])
#				if (botData[devNum][brgMAC] ~ /^88:51:fb/) {
#					botData[devNum][brgMfgr]="HP/Aruba"
#				} else if (botData[devNum][brgMAC] ~ /^00:90:e8/) {
#					botData[devNum][brgMfgr]="Moxa"
#				}
#			}
#			if (devType == "saf") {
#				devNum=(substr(devArr[3],5,7))
#				#print "safety: " devArr[1] " " devArr[2] " " devNum
#				botData[devNum][safIP]=devArr[1]
#				botData[devNum][safMAC]=devArr[2]
#			}
#			if (devType == "bot") {
#				devNum=(substr(devArr[3],4,7))
#				botData[devNum][botIP]=devArr[1]
#				#print botData[devNum][botIP]
#				botData[devNum][botMAC]=devArr[2]
#			}
#		}
#	}
#
#	# determine the default version of simba.  Assign ALL elements this version.  The overwrite with the override version for applicable bots using the simbaFile, store in array.
#	#DEFAULT_VERSION=Simba.X.2.0.8-S.5
#	#
#	#VERSION=SimbaVac_v2406
#	#bot2505
#    #
#	#VERSION=Simba.X.2.3.3
#	#bot2474
#	#bot2476
#	#bot2430
#	#...
#	while ((getline simbaVer < simbaFile) > 0) {
#		if (simbaVer ~/^DEFAULT_VERSION/) {
#			split(simbaVer,verArr,"=")
#			for (i in botData) {
#				botData[i][simba]=verArr[2]
#			}
#		}
#		if (simbaVer ~ /^VERSION/) {
#			split(simbaVer,verArr,"=")
#			altVersion=verArr[2]
#		}
#		if (simbaVer ~ /^bot....$/) {
#			devNum=substr(simbaVer,4,7)
#			botData[devNum][simba]=altVersion
#			#print devNum" "altVersion
#		}
#	}
#
#	# by now the SNMP portion has completed, read this file.  Using the IP, find the matching bridge and insert the firmware version and status (offline/online)
#	# compensates for multiple IPs in a single line (due to lack of response)
#	#2018-04-25 14:17:47 EDT,172.17.18.159,1.11.8 Build 17042115
#	#2018-04-25 14:17:54 EDT,172.17.16.163,V2.0.0.0-eng01-B0012
#	#<timestamp>,<ip>,<version>
#	# for (j in botData) {
#		# botData[j][status]="cached"
#	# }
#	while ((getline snmpLine < snmpFile) > 0) {
#		n=split(snmpLine,snmpArr,",")
#		snmpAddr=snmpArr[2]
#		snmpVersion=snmpArr[3]
#		snmpMAC=snmpArr[4]
#		botID=snmpArr[5]
#		#no conditions needed, nothing in snmpFile should exist that is not in the vlan file.
#		botData[botID][brgIP]==snmpAddr
#		botData[botID][status]="online"
#		botData[botID][brgFW]=snmpVersion
#	}
#
#	# make a CSV from array.
#	# printf "site_id,Date,Time,botID,mfgr,simba_version,brg_firmware,brg_ip,brg_mac,bot_ip,bot_mac,saf_ip,saf_mac,status\n" > outFile
#	for (j in botData) {
#		if (length(botData[j][bot]) > 1) {
#			printf siteName "," DATE_STAMP "," TIME_STAMP "," substr(botData[j][bot],4,7) "," >> outFile
#			if (botData[j][brgMfgr]=="unknown") {
#				botData[j][brgMfgr]=""
#				#***** this may need to go after oldSnmpFile handled earlier
#				while ((getline yesterLine < oldSnmpFile) > 0) {
#					split(yesterLine,yesterLineArr,",")
#					if (yesterLineArr[4] == botData[j][bot]) {
#						if (yesterLineArr[7] != "offline") {
#							botData[j][brgMfgr]=yesterLineArr[5]
#							botData[j][brgFW]=yesterLineArr[7]
#							botData[j][brgMAC]=yesterLineArr[9]
#						}
#					}
#				}
#			}
#			printf botData[j][brgMfgr] >> outFile
#			printf ","  botData[j][simba] "," >> outFile
#			printf botData[j][brgFW] "," >> outFile
#			printf botData[j][brgIP] >> outFile
#			printf "," >> outFile
#			printf botData[j][brgMAC] >> outFile
#			printf "," botData[j][botIP] "," botData[j][botMAC] "," botData[j][safIP] "," botData[j][safMAC] "," botData[j][status] "\n" >> outFile
#		}
#	}
#}
##END OF END
#'
#/LOG/wireless/get_bot_brg_saf_inventory

touch ${currentFile}
if [ -r ${outFile} -a -w ${currentFile} ]
then
	cp ${outFile} ${currentFile}
fi

rm -f ${logDir}/${yesterday}/${FILE_PREFIX}BotMaster_00000000000000.csv
rm -f /tmp/${THIS_SCRIPT}*
find ${logDir} -maxdepth 1 -type f -mtime +1 -name "get_bot_brg_saf_inventory_snmp_results.????????.csv" | xargs -I {} rm {} 2> /dev/null

######################################################################
# Standard closisg BEGINS
######################################################################
echo "$(date "+%Y-%m-%d %H:%M:%S %Z") ${THIS_SCRIPT} has finished running..."
######################################################################
# Standard closing BEGINS
######################################################################