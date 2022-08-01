"""Filters that use operations on fields."""

import re

from scheduler.api.utils import OrderedEnum
from ._base_filter import BaseFilter


class FilterOperator(OrderedEnum):
    """Filter operators."""
    EQUALS = "is"
    NOT_EQUAL = "is not"
    IN = "in"
    MATCHES = "matches"
    LESS_THAN = "less than"
    LESS_THAN_EQ = "less or equal"
    GREATER_THAN = "greater than"
    GREATER_THAN_EQ = "greater or equal"

    BASE_OPS = [EQUALS, NOT_EQUAL]  # IN not implemented yet
    STRING_OPS = [MATCHES]
    MATH_OPS = [
        LESS_THAN,
        LESS_THAN_EQ,
        GREATER_THAN,
        GREATER_THAN_EQ,
    ]
    VALUES = BASE_OPS + STRING_OPS + MATH_OPS


class FieldFilter(BaseFilter):
    """Filter that uses fields and field operators."""
    FIELD_OPERATOR_KEY = "field_operator"
    FIELD_VALUE_KEY = "field_value"

    def __init__(self, field_getter, field_operator, field_value):
        """Initialize.

        Args:
            field_getter (function): function to get a field value from
                the item we're filtering. This should accept the same
                arguments that the filter function accepts (so in the
                case of filters applied to dictionaries, it will accept
                a key and value arg).
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
        """
        super(FieldFilter, self).__init__()
        self._field_getter = field_getter
        self._field_operator = field_operator
        self._field_value = field_value

    def filter_function(self, *args, **kwargs):
        """Filter function.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        field_value = self._field_getter(*args, **kwargs)
        if self._field_operator == FilterOperator.EQUALS:
            return field_value == self._field_value
        if self._field_operator == FilterOperator.NOT_EQUAL:
            return field_value != self._field_value
        if self._field_operator == FilterOperator.IN:
            return field_value in self._field_value
        if self._field_operator == FilterOperator.MATCHES:
            return re.match(self._field_value, field_value)
        if self._field_operator == FilterOperator.LESS_THAN:
            return field_value < self._field_value
        if self._field_operator == FilterOperator.LESS_THAN_EQ:
            return field_value <= self._field_value
        if self._field_operator == FilterOperator.GREATER_THAN:
            return field_value > self._field_value
        if self._field_operator == FilterOperator.GREATER_THAN_EQ:
            return field_value >= self._field_value

    @property
    def field_operator(self):
        """Get filter field operator.

        Returns:
            (FilterOperator): the field operator.
        """
        return self._field_operator

    @property
    def field_value(self):
        """Get filter field value.

        Returns:
            (variant): the field value.
        """
        return self._field_value

    def _to_dict(self):
        """Get dict representation, excluding the class key.

        Note that this doesn't attempt to serialize the getter; the
        assumption is that subclasses will define the getter and then
        are uniquely determined by the operator and the value. For any
        subclasses where this isn't the case, _to_dict must be
        reimplemented.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.FIELD_OPERATOR_KEY: self._field_operator,
            self.FIELD_VALUE_KEY: self._field_value,
        }

    @classmethod
    def _from_dict(cls, dict_repr):
        """Get dict representation (excluding the class key).

        This assumes the subclass __init__ just requires a field operator and
        field value arg, and that the field value arg is json-serializable.
        Needs to be reimplemented otherwise.

        Args:
            dict_repr (dict): dictionary representation of class.

        Returns:
            (BaseFilter or None): filter object, if found.
        """
        if (cls.FIELD_OPERATOR_KEY not in dict_repr
                or cls.FIELD_VALUE_KEY not in dict_repr):
            return None
        field_operator = dict_repr.get(cls.FIELD_OPERATOR_KEY)
        field_value = dict_repr.get(cls.FIELD_VALUE_KEY)
        return cls(field_operator, field_value)