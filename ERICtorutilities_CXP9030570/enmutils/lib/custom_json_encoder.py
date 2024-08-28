""" Custom json encoder """

import json


class CustomEncoder(json.JSONEncoder):
    """ Custom json encoder to handle unsupported data types for json dumps method """

    def default(self, obj):  # pylint: disable=E0202
        """
        Returns a serializable object for ``obj``, or calls the base implementation
        (to raise a ``TypeError``).
        :param obj: Object to be serialized
        :type obj: object

        :returns: serializable object
        :rtype: object
        """
        NoneType = type(None)
        default_data_types = [dict, list, tuple, str, unicode, int,
                              long, float, bool, NoneType]
        if isinstance(obj, set):
            return list(obj)
        if not any([isinstance(obj, data_type) for data_type in default_data_types]):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
