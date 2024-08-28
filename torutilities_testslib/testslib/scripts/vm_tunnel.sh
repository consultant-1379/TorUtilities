#!/bin/bash
# Tunnel script to forward SSH traffic from the VM gateway to the MS

# NOTE: Ensure that the Port attribute is set to '23' in /etc/ssh/sshd_config, then restart sshd service afterwards

GATEWAY_IP=10.45.200.30
MS_IP=192.168.0.42

# Make sure we can ping the tunnel endpoint
ping -c 1 -W 2 $MS_IP > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "MS tunnel endpoint $MS_IP is pingable"
else
    echo "MS tunnel endpoint $MS_IP is not pingable"
    exit 1
fi

# Copy the public key for the gateway over to the MS
echo "Copying public key to the MS to allow public based key access"
ssh-copy-id root@${MS_IP} 

# Set up port forwarding of all SSH traffic on port 22 towards the MS
ssh -C2N -g -L 0.0.0.0:22:localhost:22 root@${MS_IP} > /dev/null 2>&1 &

if [[ $? == 0 ]]; then
    echo "SSH tunnel established: You can connect to the MS by SSHing to port 22 (default) of ${GATEWAY_IP} or to the Gateway by SSHing to port 23 of ${GATEWAY_IP}"
fi
