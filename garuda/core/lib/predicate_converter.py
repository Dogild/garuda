# -*- coding:utf-8 -*-

from pypred import parser as pypred_parser


class GAPredicateConversionError(Exception):
    """
    """
    pass


class GAPredicateConverter(object):
    """
    """
    def __init__(self):
        """
        """
        self._lexer = pypred_parser.get_lexer()
        self._parser = pypred_parser.get_parser()

    def convert(self, source):
        """
        """

        ast = self._parser.parse(source, self._lexer)

        if self._parser.errors or self._lexer.errors:
            raise GAPredicateConversionError("Could not convert due to the following errors %s" % (self._parser.errors + self._lexer.errors))

        return self._convert_tree(ast)

    def _convert_tree(self, ast):
        """
        """
        raise NotImplemented('%s should override _convert_tree method.')