#!/bin/bash

##################################################################################################
# This script is a modified version of limitbw in NETSim repo ERICnetsimpmcpp_CXP9029065         #
# Most of the unecessary functionality has been removed.                                         #
# The Linux utilities tc, ethtool and iptables is what limitbw uses.                             #
##################################################################################################


removeTrafficControls()
{
    # Clear any existing traffic controls
    /usr/sbin/tc qdisc del \
        dev ${NET_IF} \
        root > /dev/null 2>&1

    ${IPTABLES} --table mangle --flush  > /dev/null 2>&1
    ${IP6TABLES} --table mangle --flush  > /dev/null 2>&1
}


processNode() {

    # MY VARIABLES
    MY_IP=$1
    MY_SIM=$2
    DELAY=$3
    BANDWIDTH=$4
    MY_PARENT=$5
    MY_INDEX=$6

    # Create the queue with the specified bandwidth
    CLASS_ID=1:${MY_INDEX}
    /usr/sbin/tc class add \
        dev ${NET_IF} \
        parent ${MY_PARENT} \
        classid ${CLASS_ID} \
        htb rate ${BANDWIDTH}kbit
    if [ $? -ne 0 ] ; then
        echo "ERROR: Failed to define bandwidth class for ${MY_IP}"
        exit 1
    fi

    # Create the qdisc to add the delay
    DELAY_QDISC_NUM=`expr ${MY_INDEX} + 1`
    DELAY_QDISC="${DELAY_QDISC_NUM}:"
    /usr/sbin/tc qdisc add \
        dev ${NET_IF} \
        parent ${CLASS_ID} \
        handle ${DELAY_QDISC} \
        netem delay ${DELAY}ms
    if [ $? -ne 0 ] ; then
        echo "ERROR: Failed to define delay qdisc for ${MY_IP}"
        exit 1
    fi

    # Now we need to get packets going to the IP address
    # added class for that address
    echo "${MY_IP}" | grep : > /dev/null
    if [ $? -eq 0 ] ; then
        IPTABLES_CMD=${IP6TABLES}
    else
        IPTABLES_CMD=${IPTABLES}
    fi
    ${IPTABLES_CMD} -t mangle -A POSTROUTING \
        -s ${MY_IP} \
        -j CLASSIFY --set-class ${CLASS_ID}
    if [ $? -ne 0 ] ; then
        echo "ERROR: Failed to define iptables rule for ${MY_IP}"
        exit 1
    fi
} # END processNode


applyTrafficControls()
{

    # Make sure TSO is disabled
    TSO_STATUS=`${ETHTOOL} -k ${NET_IF} | egrep '^tcp segmentation offload' | awk '{print $NF}'`
    if [ "${TSO_STATUS}" = "on" ] ; then
        echo " Disabling TSO on ${NET_IF}"
        ${ETHTOOL} -K ${NET_IF} tso off
    fi

    # Create a root htb qdisc
    /usr/sbin/tc qdisc add \
        dev ${NET_IF} \
        handle 1: \
        root \
        htb default 0
    if [ $? -ne 0 ] ; then
        echo "ERROR: Failed to create root htb qdisc"
        exit 1
    fi

    # Create default class with full bandwidth of NIC
    NIC_BANDWIDTH=`${ETHTOOL} ${NET_IF} | awk '{if ($1 == "Speed:") print $2}' | sed 's|Mb/s||'`
    /usr/sbin/tc class add \
        dev ${NET_IF} \
        parent 1: \
        classid 1:0 \
        htb rate ${NIC_BANDWIDTH}mbit

    # Read in the file, split the line in each file and then call processNode
    MY_PARENT=1:0
    INDEX=1
    while read -r line
    do
        result=$(echo $line | tr ',' '\n')
        processNode $result $MY_PARENT $INDEX
        INDEX=`expr ${INDEX} + 1`

    done < $BANDWITH_INFO_FILE

} # END applyTrafficControls


showTrafficControls()
{
    ${IPTABLES} --table mangle --list --numeric > /tmp/iptables.txt 2>&1
    ${IP6TABLES} --table mangle --list --numeric > /tmp/iptables6.txt 2>&1
	#Including support for DSC, TCU03 (STN)
    su - netsim -c "echo '.show started' | /netsim/inst/netsim_pipe" | sort > /tmp/nodes.txt
    /usr/sbin/tc qdisc show dev ${NET_IF} > /tmp/node_delay.txt

   # Fetch and store the bandwidth
   /usr/sbin/tc class show dev ${NET_IF} | sort -n -k 7 > /tmp/node_bw.txt

    NF=`head -1 /tmp/node_bw.txt  | awk '{print NF}'`
    printf "%-20s %-10s %-10s %-15s %s\n" "NODE" "BANDWIDTH" "DELAY" "IPADDRESS" "NET_IF"
    while read line; do
        CLASS=`echo ${line} | awk '{print $3}'`
        if [ "${CLASS}" != "1:" ] ; then

            if [ $NF -ne 16 ] ; then
                BANDWIDTH=`echo ${line} | awk '{print $11}'`
            else
	        BANDWIDTH=`echo ${line} | awk '{print $10}'`
	    fi
            IPADDRESS=`cat /tmp/iptables.txt | awk -v MATCH="$CLASS" '{if ($NF == MATCH) print $4}'`
            if [ -z "${IPADDRESS}" ] ; then
                IPADDRESS=`cat /tmp/iptables6.txt | awk -v MATCH="$CLASS" '{if ($NF == MATCH) print $3}' | sed 's|/.*$||'`
            fi

            DELAY=`cat /tmp/node_delay.txt | awk -v MATCH="$CLASS" '{if ($5== MATCH) print $9}'`

            if [ ! -z "${IPADDRESS}" ] ; then
                NODE=`cat /tmp/nodes.txt | awk -v IP=$IPADDRESS '{if ($2 == IP) print $1}'`
                printf "%-20s %-10s %-10s %-15s %s\n" ${NODE} ${BANDWIDTH} ${DELAY} ${IPADDRESS} ${NET_IF}

            fi

        fi
    done < /tmp/node_bw.txt

} # END showTrafficControls



###############
# MAIN METHOD #
###############

BANDWITH_INFO_FILE="/tmp/BANDWITH_INFO_FILE.txt"
NETSIM=0
OP=$1

if [ -r /usr/sbin/ethtool ] ; then
    ETHTOOL=/usr/sbin/ethtool
elif [ -r /sbin/ethtool ] ; then
    ETHTOOL=/sbin/ethtool
else
    echo "ERROR: Cannot file ethtool"
    exit 1
fi

IPTABLES=/usr/sbin/iptables
IP6TABLES=/usr/sbin/ip6tables

# Need to figure out which interface to use,
# interface used for default destination
NET_IF=`/sbin/route  | egrep "^default" | awk '{ print $NF }'`

# IPv6 doesn't show :x nics
if [ -z "${NET_IF}" ] ; then
    NET_IF="eth0"
fi

if [ "${OP}" = "-s" ] ; then
    removeTrafficControls
    applyTrafficControls
    showTrafficControls
elif [ "${OP}" = "-r" ] ; then
    removeTrafficControls
fi







