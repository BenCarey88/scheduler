"""Filters that use operations on fields."""

import fnmatch

from scheduler.api.common import BaseDateTimeWrapper
from scheduler.api.enums import OrderedStringEnum
from ._base_filter import BaseFilter


class FilterOperator(OrderedStringEnum):
    """Filter operators."""
    EQUALS = "Is"
    NOT_EQUAL = "Is Not"
    IN = "In"
    MATCHES = "Matches"
    DOESNT_MATCH = "Does not Match"
    STARTS_WITH = "Starts With"
    ENDS_WITH = "Ends With"
    LESS_THAN = "Less Than"
    LESS_THAN_EQ = "Less or Equal"
    GREATER_THAN = "Greater Than"
    GREATER_THAN_EQ = "Greater or Equal"

    @classmethod
    def get_base_ops(cls):
        return [cls.EQUALS, cls.NOT_EQUAL]  # IN not implemented yet

    @classmethod
    def get_string_ops(cls):
        return [
            cls.MATCHES,
            cls.DOESNT_MATCH,
            cls.STARTS_WITH,
            cls.ENDS_WITH,
        ]

    @classmethod
    def get_maths_ops(cls):
        return [
            cls.LESS_THAN,
            cls.LESS_THAN_EQ,
            cls.GREATER_THAN,
            cls.GREATER_THAN_EQ,
        ]

    @classmethod
    def get_all_ops(cls):
        return cls.get_base_ops() + cls.get_string_ops() + cls.get_maths_ops()


class FieldFilter(BaseFilter):
    """Filter that uses fields and field operators."""
    FIELD_OPERATOR_KEY = "field_operator"
    FIELD_VALUE_KEY = "field_value"

    def __init__(
            self,
            field_getter,
            field_operator,
            field_value,
            math_ops_key=None):
        """Initialize.

        Args:
            field_getter (function): function to get a field value from
                the item we're filtering. This should accept the same
                arguments that the filter function accepts (so in the
                case of filters applied to dictionaries, it will accept
                a key and value arg).
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
            math_ops_key (function or None): function to convert field
                to a numeric value for maths ops, if needed.
        """
        super(FieldFilter, self).__init__()
        self._field_getter = field_getter
        self._field_operator = field_operator
        self._field_value = field_value
        self._field_maths_value = field_value
        self._math_ops_key = math_ops_key
        if (math_ops_key is not None and
                field_operator in FilterOperator.get_maths_ops()):
            self._field_maths_value = math_ops_key(field_value)

    def _filter_function(self, *args, **kwargs):
        """Filter function.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        field_value = self._field_getter(*args, **kwargs)
        field_maths_value = field_value
        if (self._math_ops_key is not None and
                self._field_operator in FilterOperator.get_maths_ops()):
            field_maths_value = self._math_ops_key(field_value)
            if not isinstance(field_maths_value,
                    (int, float, BaseDateTimeWrapper)):
                return False

        if self._field_operator == FilterOperator.EQUALS:
            return field_value == self._field_value
        if self._field_operator == FilterOperator.NOT_EQUAL:
            return field_value != self._field_value
        if self._field_operator == FilterOperator.IN:
            return field_value in self._field_value
        if self._field_operator == FilterOperator.MATCHES:
            return fnmatch.fnmatch(field_value, self._field_value)
        if self._field_operator == FilterOperator.DOESNT_MATCH:
            return not fnmatch.fnmatch(field_value, self._field_value)
        if self._field_operator == FilterOperator.STARTS_WITH:
            return field_value.startswith(self._field_value)
        if self._field_operator == FilterOperator.ENDS_WITH:
            return field_value.endswith(self._field_value)
        if self._field_operator == FilterOperator.LESS_THAN:
            return field_maths_value < self._field_maths_value
        if self._field_operator == FilterOperator.LESS_THAN_EQ:
            return field_maths_value <= self._field_maths_value
        if self._field_operator == FilterOperator.GREATER_THAN:
            return field_maths_value > self._field_maths_value
        if self._field_operator == FilterOperator.GREATER_THAN_EQ:
            return field_maths_value >= self._field_maths_value

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
        subclasses where this isn't the case, _to_dict and _from_dict must
        be reimplemented.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.FIELD_OPERATOR_KEY: self._field_operator,
            self.FIELD_VALUE_KEY: self._field_value,
        }

    @classmethod
    def _from_dict(cls, dict_repr):
        """Initialize class from dict representation.

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
