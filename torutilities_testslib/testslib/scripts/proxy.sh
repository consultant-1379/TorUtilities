#!/bin/bash

TUNNEL_ENDPOINT="atclvm709.athtem.eei.ericsson.se"
PROXIES=(153.88.253.150 164.48.228.114 138.85.242.5)

### make sure we can ping the tunnel endpoint ###
ping -c 1 -W 2 $TUNNEL_ENDPOINT > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Tunnel endpoint $TUNNEL_ENDPOINT is pingable"
else
    echo "Tunnel endpoint $TUNNEL_ENDPOINT is not pingable"
    exit 1
fi

for PROXY in "${PROXIES[@]}"; do
    ping -c 1 -W 2 $PROXY > /dev/null 2>&1
    if [ $? -eq 0 ]; then
	echo "Proxy host $PROXY is pingable..."
        ssh -C2TN -L 0.0.0.0:9999:${PROXY}:8080 root@${TUNNEL_ENDPOINT} > /dev/null 2>&1 &
	echo "Proxy established: localhost:9999 -> ${PROXY}:8080"
	echo "Please run: 'export http_proxy=http://localhost:9999'"
	break
    else
	echo "Proxy host $PROXY is not pingable"
    fi
done
