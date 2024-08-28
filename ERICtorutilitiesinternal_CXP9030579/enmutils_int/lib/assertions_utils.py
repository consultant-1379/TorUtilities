# ********************************************************************
# Name    : Assertions Utility
# Summary : Module used for utilities needed for the assertion
#           framework.
# ********************************************************************

from datetime import datetime
from enmutils_int.lib.common_utils import LimitedSizeDict
from enmutils.lib import persistence


class AssertionValues(object):
    """
    Object for the persisting of a assertion values.
    """
    KEY = "{0}_assertion_values"

    def __init__(self, profile_name, size_limit=1000):
        """
        :param profile_name: name of the profile.
        :type profile_name: str
        """
        self.profile_name = profile_name
        self.size_limit = size_limit

    def _teardown(self):
        """
        Teardown method
        :rtype: None
        """
        self.delete()

    @property
    def values(self):
        """
        Gets the assertion values from persistence
        :rtype: dict
        """

        return persistence.get(self.KEY.format(self.profile_name))

    def delete(self):
        """
        Deletes the assertion values from persistence.
        :rtype: None
        """
        persistence.remove(self.KEY.format(self.profile_name))

    def update(self, value, date_time=None):
        """
        :param date_time: the date and time
        :type date_time: datetime.datetime
        :param value: value to persist
        :type value: any
        :rtype: None
        """
        asserts_dict = self.values
        if not date_time:
            date_time = datetime.now()

        if not asserts_dict:
            asserts_dict = LimitedSizeDict(size_limit=self.size_limit)

        asserts_dict[date_time] = value

        persistence.set(self.KEY.format(self.profile_name), asserts_dict, -1, log_values=False)
