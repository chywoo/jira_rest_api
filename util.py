__author__ = 'chywoo.park'


class VersatileDict:
    """
    Manipulate multiple layered multiple data type.
    """
    data = None

    def __init__(self, obj):
        if isinstance(obj, self.__class__):
            self.data = obj.data
        else:
            self.data = obj

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __setattr__(self, key, value):
        if self.__dict__.get("_locked") and key == "data":
            raise AttributeError, "VersatileDict does not allow assignment to .data memeber."
        self.__dict__[key] = value

    def to_string(self):
        return repr(data)

    def value(self, keystring=None):
        """
        Get value from JSON format data. Input key path(key1/key2/key3) and get the value.
        :param keystring: Key path
        :return: Value
        """

        if keystring is None:
            return self.data

        result = self.data

        keys = keystring.split("/")

        for key in keys:
            if isinstance(result, dict):
                result = result[key]
            elif isinstance(result, list):
                try:
                    result = result[int(key)]
                except ValueError as e:
                    raise KeyError("'%s' is not index value of List. Type of the value is List. Index must be integer." % key)

        return result