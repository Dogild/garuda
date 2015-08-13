# -*- coding: utf-8 -*-


class GAPropertyError(object):
    """

    """

    def __init__(self, type, property):
        """
        """
        self.type = type
        self.property = property
        self.errors = []

    def add_error(self, title, description, suggestion):
        """
        """
        self.errors.append(GAError(title=title, description=description, suggestion=suggestion))

    def add_errors(self, errors):
        """
        """
        for error in errors:
            self.errors.append(error)

    def to_dict(self):
        """
        """
        d = dict()

        d['property'] = self.property
        d['type'] = self.type
        d['descriptions'] = [error.to_dict() for error in self.errors]  # descriptions to match VSD behavior

        return d


class GAError(object):
    """
    """
    TYPE_INVALID = 'invalid'
    TYPE_NOTFOUND = 'not found'
    TYPE_CONFLICT = 'conflict'
    TYPE_UNKNOWN = 'unknown'
    TYPE_NOTALLOWED = 'not allowed'

    def __init__(self, title, description, suggestion):
        """
        """
        self.title = title
        self.description = description
        self.suggestion = suggestion

    def to_dict(self):
        """
        """
        d = dict()

        d['title'] = self.title
        d['description'] = self.description
        d['suggestion'] = self.suggestion

        return d


class GAErrorsList(list):
    """
    """
    def __init__(self):
        """
        """
        self.type = None

    def add_error(self, type, property, title, description, suggestion=None):
        """
        """
        self.type = type
        property_error = self._get_property_error(property)

        if property_error is None:
            property_error = GAPropertyError(type=type, property=property)
            self.append(property_error)

        property_error.add_error(title=title, description=description, suggestion=suggestion)

    def merge(self, error_list):
        """
        """
        for perror in error_list:
            property_error = self._get_property_error(perror.property)

            if property_error is None:
                self.append(perror)
            else:
                property_error.add_errors(perror.errors)

    def _get_property_error(self, property):
        """
        """
        for error in self:
            if error.property == property:
                return error

        return None

    def has_errors(self):
        """
        """
        return self.type or len(self) > 0

    def clear(self):
        """
        """
        del self[:]
        self.type = None

    def to_dict(self):
        """
        """
        return [error.to_dict() for error in self]