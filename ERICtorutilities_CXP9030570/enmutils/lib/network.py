# ********************************************************************
# Name    : Network
# Summary : Generic network related functionality, not related to the
#           network tool.
# ********************************************************************

import socket

from contextlib import closing
import persistence


def get_fqdn(host):
    """
    B{Gets fully-qualified domain name from the specified IP or hostname}

    :type host: str
    :param host: Hostname or IP address to get the FQDN of
    :rtype: str
    :return: persistance key if persistance have any or fqdn
    """

    key = "{0}-fqdn".format(host)

    # If we've already checked this host before, and have persisted data, return that
    if persistence.has_key(key):
        return persistence.get(key)

    # Otherwise, figure out the data
    fqdn = None

    fqdn = socket.getfqdn(socket.gethostbyaddr(host)[0])
    if fqdn is not None and len(fqdn) > 0:
        persistence.set(key, fqdn.strip(), 1800)

    return fqdn


def is_port_open(ip_addr, port):
    """
     B{Checks if a port is open on a specific ip address}

     :type ip_addr: str
     :param ip_addr: Hostname or IP address to get the FQDN of
     :type port: int
     :param port: Port number
     :rtype: bool
     :return: True if connection is opened else False
     :raises RuntimeError: raises if ip address is not valid
     """

    if not is_valid_ip(ip_addr):
        raise RuntimeError("{ip_addr} is not a valid ip address".format(ip_addr=ip_addr))

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((ip_addr, port)) == 0


def is_valid_ip(ip):
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def is_valid_ipv6(ipv6_string):
    """
    B{Returns true if a string is a valid IPv6 address}

    :type ipv6_string: str
    :param ipv6_string: String to be validated
    :rtype: bool
    :return: True if there is no socket error else False
    """

    try:
        socket.inet_pton(socket.AF_INET6, ipv6_string)
        return True
    except socket.error:
        return False


def is_valid_ipv4(ipv4_string):
    """
    B{Returns true if a string is a valid IPv4 address}

    :type ipv4_string: str
    :param ipv4_string: String to be validated
    :rtype: bool
    :return: True if there is no socket error else False
    """

    try:
        socket.inet_pton(socket.AF_INET, ipv4_string)
        return True
    except socket.error:
        return False


def is_ipv4_address_private(ip):
    """
    B{Analyzes an IPv4 address and determines if it is a private address}

    :type ip: str
    :param ip: IPv4 address
    :rtype: boolean
    :return: True if ipv4 is valid else False
    """

    ip = ip.strip()
    result = False

    if ip.startswith("127.") or ip.startswith("192.168"):
        if is_valid_ipv4(ip):
            result = True
    elif ip.startswith("172."):
        if is_valid_ipv4(ip):
            temp_list = ip.split(".")
            if (int(temp_list[1]) >= 16) and (int(temp_list[1]) <= 31):
                result = True

    return result


def is_multicast_ipv4(ipv4_address):
    """
    B{Checks if an IPv4 address is between 224.0.0.0 and 239.255.255.255}

    :type ipv4_address:string
    :param ipv4_address: String representation of an IPv4 address
    :rtype: boolean
    :return: True if ipv4 is valid and if firts octet value is less than 223 else False
    """

    is_multicast = False

    try:
        if is_valid_ipv4(ipv4_address):
            first_octet_value = int(ipv4_address.split('.', 1)[0])
            if 223 < first_octet_value <= 239:
                is_multicast = True
    except ValueError:
        pass

    return is_multicast
