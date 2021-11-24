"""Utils for tests."""

from collections import OrderedDict


def create_ordered_dict_from_tuples(tuples_list, ordered_dict=None):
    """Create a nested ordered dict from a nesting of tuples and lists.

    This is just easier to write than constantly having to write OrderedDict
    over and over.

    Note that this will not allow us to create dictionaries with list values
    as these get interpreted as subdicts.

    Example input format:
    [
        ("a", "A"),
        ("b", "B"),
        (
            "c", [
                ("d", "D"),
                ("e", "E")
            ]
        )
    ])

    Args:
        tuples_list (list): list of tuples, representing key, value pairs.
        ordered_dict (OrderedDict or None): used when calling function
            recursively to build up ordered dict.

    Returns:
        (OrderedDict): the ordered dict represented by the string.
    """
    ordered_dict =  ordered_dict if ordered_dict is not None else OrderedDict()
    for key, value in tuples_list:
        if isinstance(value, list):
            ordered_dict[key] = OrderedDict()
            create_ordered_dict_from_tuples(value, ordered_dict[key])
        else:
            ordered_dict[key] = value
    return ordered_dict
