# ********************************************************************
# Name    : Helper Methods
# Summary : Functional module with a simple helper method to generate
#           a simple dictionary from a list. Should only be used for
#           generic helper functions which can be reused anywhere and
#           should not import from anywhere.
# ********************************************************************

import commands
import time
import socket


def list_netsim_simulations(max_retries=0, lte_match=True):
    """
    Retrieve the list of netsim simulations

    :param max_retries: Retry counter
    :type max_retries: int
    :param lte_match: Boolean indicating if the list of sims should include at least one ERBS * 40 node simulation
    :type lte_match: bool

    :return: List of simulations found
    :rtype: list
    """
    cmd = "/opt/ericsson/nssutils/bin/netsim list netsim --no-ansi"
    rc, output = commands.getstatusoutput(cmd)
    if not rc:
        if (lte_match and not any([sim.strip() for sim in output.split("\n")[3:] if
                                   'LTE' in sim and 'limx40' in sim]) and max_retries < 3):
            max_retries += 1
            list_netsim_simulations(max_retries=max_retries, lte_match=lte_match)
        return [sim.strip() for sim in output.split("\n")[3:]]
    if max_retries < 1:
        time.sleep(30)
        list_netsim_simulations(max_retries=1, lte_match=lte_match)


def generate_basic_dictionary_from_list_of_objects(list_to_be_converted, name_of_attr_to_be_key):
    """
    Creates a dictionary object from the supplied list based upon by the supplied key attribute

    :param list_to_be_converted: List of objects to be sorted into the dict based upon the key
    :type list_to_be_converted: list
    :param name_of_attr_to_be_key: Name of the attribute on each object to sort upon
    :type name_of_attr_to_be_key: str

    :returns: Dictionary created from the supplied values
    :rtype: dict
    """
    generated_dict = {}
    for _ in list_to_be_converted:
        key = getattr(_, name_of_attr_to_be_key)
        if key not in generated_dict.keys():
            generated_dict[key] = []
        generated_dict[key].append(_)
    return generated_dict


def get_local_ip_and_hostname(get_ip=True):
    """
    Gets the hostname and optionally the IP of the host machine

    :param get_ip: boolean of whether to run the command to get the ip address of the host machine
    :type get_ip: bool

    :rtype: tuple
    :return: Index 0 is the IP and index 1 is hostname

    :raises RuntimeError: raised if cannot get the local IP address
    """
    ip = ""
    error_message = "Could not get the {0}."
    hostname = socket.gethostname()
    if not hostname:
        raise RuntimeError(error_message.format('hostname'))

    if get_ip:
        ip = socket.gethostbyname_ex(hostname)[-1][-1]
        if not ip:
            raise RuntimeError(error_message.format('local IP'))

    return ip, hostname
