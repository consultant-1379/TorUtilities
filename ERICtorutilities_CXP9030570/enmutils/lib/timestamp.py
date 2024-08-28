# ********************************************************************
# Name    : Timestamp
# Summary : Wrapper functionality around datetime and time instances.
# ********************************************************************

import datetime
import time
import calendar
import log


def is_time_current(datetime_obj):
    """
    Checks if the time(hours and minutes) of the datetime object passed in matches the current time.

    :param datetime_obj: datetime.datetime object
    :type datetime_obj: datetime.datetime
    :return: True if time is current else False
    :rtype: bool
    """

    result = False
    now = get_current_time()
    if now.hour == datetime_obj.hour and now.minute == datetime_obj.minute:
        result = True

    return result


def get_current_time():
    """
    B{Returns a datetime object with the current time}.
    :return: datetime object
    :rtype: datetime.datetime
    """

    return datetime.datetime.now()


def get_elapsed_time(start_time):
    """
    B{Returns the elapsed time between the current time and the specified start time as a decimalized string}

    :type start_time: datetime object
    :param start_time: The start time to use for computing the elapsed time
    :return: elapsed time
    :rtype: str
    """

    elapsed_time = datetime.datetime.now() - start_time
    return get_string_elapsed_time(elapsed_time)


def get_elapsed_time_in_seconds(elapsed_time):
    """
    B{Converts an elapsed time in the form of a datetime.timedelta object to the total number of seconds}

    :type elapsed_time: datetime.timedelta object
    :param elapsed_time: The elapsed time (datetime.timedelta) to be converted into seconds
    :rtype: int
    :return: elapsed time in seconds
    """

    return (elapsed_time.microseconds + (float(elapsed_time.seconds) + elapsed_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def get_string_elapsed_time(elapsed_time):
    """
    B{Converts the datetime.timedelta passed as a parameter to an elapsed time string rounded to 3 decimal places}

    :type elapsed_time: datetime.timedelta object
    :param elapsed_time: The elapsed time (datetime.timedelta) to be stringified
    :rtype: str
    :return: elapsed time as string
    """

    total_seconds = get_elapsed_time_in_seconds(elapsed_time)
    elapsed_time = "%.3f" % total_seconds
    return elapsed_time


def is_time_diff_greater_than_time_frame(start_time, end_time, time_frame):
    """
    Checks if the difference between the start and end time exceeds a given time frame

    :param start_time: datetime object
    :type start_time: datetime.datetime
    :param end_time: datetime object
    :type end_time: datetime.datetime
    :param time_frame: int, seconds
    :type time_frame: int

    :return: True if the difference exceeds the time frame else False
    :rtype: bool
    """

    return (end_time - start_time) > datetime.timedelta(seconds=time_frame)


def get_elapsed_time_in_duration_format(start_time, completion_time):
    """
    B{Returns the elapsed time between the current time and the specified start time as a float}

    :type start_time: datetime object
    :param start_time: The start time to use for computing the time_diff
    :type completion_time: datetime object
    :param completion_time: The current time to use for computing the time_diff
    :rtype: str
    :return: duration in string format h:m:s
    """

    time_diff = ""
    elapsed_time = completion_time - start_time

    total_sec = str(elapsed_time.seconds % 60)
    total_min = str((elapsed_time.seconds % 3600) // 60)
    total_hour = str(elapsed_time.days * 24 + elapsed_time.seconds // 3600)

    if elapsed_time.seconds < 60:
        time_diff = "{0} sec".format(total_sec)
    else:
        time_diff = total_hour + "h:" + total_min + "m:" + total_sec + "s"

    return time_diff


def get_human_readable_timestamp(ts=None):
    """
    B{Returns the current time in a human readable format of YYYY/MM/DD HH:MM:SS}

    :return: timestamp
    :rtype: str
    """
    date = ts or datetime.datetime.now()
    return date.strftime('%Y/%m/%d %H:%M:%S')


def get_int_time_in_secs_since_epoch():
    """
    Return the number of seconds (rounded down to nearest integer) since the Epoch
    :return: Number of seconds
    :rtype: int
    """
    return int(time.time())


def convert_time_to_ms_since_epoch(convert_date, convert_time):
    """

    Return the EPOCH time in ms
    :param convert_date: date
    :type  convert_date: string
    :param convert_time: time
    :type convert_time: string
    :return: time in milliseconds
    :rtype: int

    """
    epoch_time = calendar.timegm(
        datetime.datetime.strptime(convert_date + ' ' + convert_time,
                                   '%Y-%m-%d %H:%M:%S').timetuple()) * 1000
    return epoch_time


def convert_datetime_to_str_format(datetime_obj, pattern=None):
    """
    Convert datetime object to a formatted string

    :param datetime_obj: Datetime object to be formatted as str
    :type datetime_obj: `datetime.datetime`
    :param pattern: Format of the string to be returned
    :type pattern: str

    :return: String format of the datetime object or the original object if is not formattable
    :rtype: str | original object
    """
    pattern = pattern if pattern else "%d-%b, %H:%M:%S"
    if isinstance(datetime_obj, datetime.datetime):
        log.logger.debug("Returning datetime string format time object.")
        return datetime_obj.strftime(pattern)
    else:
        log.logger.debug("Cannot convert object of type: [{0}] to datetime string format time."
                         .format(type(datetime_obj)))
        return datetime_obj


def convert_str_to_datetime_object(datetime_str, pattern=None):
    """
    Convert string object to a datetime object
    :param datetime_str: String object to be converted to datetime object
    :type datetime_str: str
    :param pattern: Format of the datetime to be returned
    :type pattern: str

    :return: Datetime object if the object can be converted, else original str
    :rtype: `datetime.datetime` | str
    """
    pattern = pattern if pattern else "%d-%b, %H:%M:%S"
    try:
        return datetime.datetime.strptime(datetime_str, pattern)
    except (ValueError, TypeError) as e:
        log.logger.debug("Cannot convert object error encountered:: [{0}].".format(str(e)))
        return datetime_str
