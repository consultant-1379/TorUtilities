
# ********************************************************************
# Name    : Arguments
# Summary : Provides generic functionality for common/repetitive tasks.
# ********************************************************************

import re
import string
from random import choice

from enmutils.lib import exception


def get_numeric_range(number_range):
    """
    Returns the start and end index from the specified range [inclusively]

    NOTE: If a single number is specified rather than a range then the start and end range will be set to this.

    @type number_range: str
    @param number_range: String representation of a range ex. 5-10, or simply a number if no range given
    @rtype: tuple
    @return: Tuple where index 0 is the start range and index 1 is the end range
    """

    lower_bound = None
    upper_bound = None

    if isinstance(number_range, str):
        if "-" not in number_range:
            try:
                lower_bound = int(number_range)
                upper_bound = int(number_range)
            except ValueError:
                pass
        else:
            range_bounds = number_range.split("-")

            if len(range_bounds) == 2:
                try:
                    lower_bound = int(range_bounds[0].strip())
                    upper_bound = int(range_bounds[1].strip())
                except ValueError:
                    pass

    # Validate the range and exit if the range isn't valid
    validate_range(lower_bound, upper_bound)

    return lower_bound, upper_bound


def get_email_addresses(email_addresses):
    """
    Processes user-specified email addresses

    @type email_addresses: str
    @param email_addresses: Comma-delimited list of one or more email addresses
    @rtype: list
    @return: validated_emails
    """

    # If we have been given more than one address, split them out
    if not isinstance(email_addresses, str):
        addresses = [str(email_addresses)]
    elif "," in email_addresses:
        addresses = email_addresses.split(",")

        # Silently remove any duplicates (don't fail)
        addresses = list(set(addresses))
    else:
        addresses = [email_addresses]

    # Remove any whitespace
    addresses = [address.strip() for address in addresses]

    # Iterate over the email addresses and make sure that each one is valid
    for address in addresses:
        validate_email_address(address)

    return addresses


def get_random_string(size=8, exclude=None, password=False, include_punctuation=False):
    """
    Generates a random string of the specified size (defaults to 8 characters)

    :param size: Number of characters to include in random string
    :type size: int
    :param exclude: Characters that are to be excluded from selection
    :type exclude: str
    :param password: Checks if its password
    :type password: bool
    :param include_punctuation: Include punctuation characters
    :type include_punctuation: bool

    :return: chars
    :rtype: str
    """

    characters = (string.ascii_letters + string.digits + string.punctuation if include_punctuation
                  else string.ascii_letters + string.digits)
    if exclude is not None:
        for char in exclude:
            characters = characters.replace(char, "")

    chars = ''.join(choice(characters) for _ in range(size))
    if password:
        chars = chars[:-4] + "H.8z"

    return chars


def grouper(sequence, n):
    return zip(*[iter(sequence)] * n)


def split_list_into_chunks(l, chunk_size):
    """
    :param l: list that needs to be split
    :type l: list
    :param chunk_size: size to what chunks the list will be separated
    :type chunk_size: int
    :return: split list
    :rtype: list[list]
    """
    return [l[i:i + chunk_size] for i in xrange(0, len(l), chunk_size)]


def validate_email_address(email_address):
    """
    Validates that the user-specified email addresses is properly formatted

    :type email_address: string
    :param email_address: Email address
    """

    if not is_valid_email_address(email_address):
        exception.handle_invalid_argument(
            "The specified email address ({0}) is not formatted correctly".format(email_address))


def validate_range(range_start, range_end):
    """
    Validates the specified range ex. '5-10'

    NOTE: Negative ranges are not supported, all values must be positive
    NOTE: Range is inclusive of end values

    :type range_start: int
    :param range_start: Start of the range
    :type range_end: int
    :param range_end: End of the range
    """

    if not is_valid_range(range_start, range_end):
        exception.handle_invalid_argument(
            "The specified numerical range ({0}-{1}) is not formatted correctly".format(range_start, range_end))


def validate_version_number(version_number):
    """
    Validates that the specified version number is formatted correctly

    :type version_number: string
    :param version_number: the version number that needs to be checked
    """
    if not is_valid_version_number(version_number):
        exception.handle_invalid_argument(
            "The specified version number ({0}) is not formatted correctly".format(version_number))


def is_valid_hostname(hostname):
    """
    Verifies that the provided hostname is valid

    :type hostname: str
    :param hostname: Hostname to validate
    :rtype: bool
    :return: Whether or not the provided hostname is valid
    """
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        # Strip exactly one dot from the right, if present
        hostname = hostname[:-1]

    # Non-highest level components of a hostname can be alphanumeric and have dashes (e.g. host1-23.athtem.999.ericsson')
    valid_hostname_component_pattern = re.compile(r'(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)
    non_top_level_components_are_valid = all(
        valid_hostname_component_pattern.match(hostname_component) for hostname_component in hostname.split(".")[:-1])

    # Highest level component in the hostname can not be entirely numeric
    valid_top_level_component_pattern = re.compile(r'(?!^\d+$)^.+$', re.IGNORECASE)
    top_level_component_is_valid = bool(valid_top_level_component_pattern.match(hostname.split(".")[-1]))

    return non_top_level_components_are_valid and top_level_component_is_valid


def is_valid_version_number(version_number):
    """
    Verifies the format of a version number

    :type version_number: str
    :param version_number: the version number that needs to be checked
    :rtype: boolean
    :return: True if is valid version number else False
    """

    result = True

    try:
        # Check that the version number contains only numbers and dots
        if "-" in version_number or not re.match(r"[\d.]", version_number):
            result = False
    except AttributeError:
        result = False

    return result


def is_valid_email_address(address):
    """
    Verifies that the user-specified email address is correctly formatted

    :type address: str
    :param address: Email address to verify
    :rtype: bool
    :return: True if is valid email address else False
    """

    result = False
    if isinstance(address, str) and re.match(r"^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$", address) \
            and len(address) <= 255:
        result = True

    return result


def is_valid_range(range_start, range_end):
    """
    Verifies the specified range ex. '5-10'

    NOTE: Negative ranges are not supported, all values must be positive
    NOTE: Range is inclusive of end values

    :type range_start: int
    :param range_start: Start of the range
    :type range_end: int
    :param range_end: End of the range
    :rtype: bool
    :return: True if its in valid range else False
    """

    result = False

    if isinstance(range_start, int) and isinstance(range_end,
                                                   int) and range_start >= 0 and range_end >= 0 and range_end >= range_start:
        result = True
    return result
