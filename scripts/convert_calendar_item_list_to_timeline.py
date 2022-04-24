"""Convert list of calendar items to Timeline item."""

from collections import OrderedDict

from scheduler.api.common.timeline import Timeline


def convert_list_to_timeline(item_list):
    """Convert calendar item list to Timeline item.

    This is intended to convert the previous way calendar items
    were stored to the new intended method. Previously they were
    stored like so on each calendar_day:

    [
        CalendarItem,
        CalendarItem,
        ...
    ]

    The current new plan is to store them like this:

    Timeline.from_dict(
        OrderedDict({
            Time: [
                CalendarItem,
                ...
            ],
            Time: [
                CalendarItem,
                ...
            ],
            ...
        })
    )

    Args:
        item_list (list(CalendarItem)): list of calendar items,
            as described above.

    Returns:
        (Timeline): timeline of calendar items, as described above.
    """
    timeline_dict = OrderedDict()
    for item in item_list:
        timeline_dict[item].setde
    # QUESTION: Do we actually want to organise calendar items in a timeline?
    # sounds like it would be useful to have this but can't currently think
    # of any advantage it gives us (except maybe ability to search for items by
    # time which could be useful?) and can think of one definite disadvantage
    # which is that current implementation means that whichever calendar item
    # has been most recently added/moved will be on top so allows user to
    # reorder to put a given item on top. With Timeline this becomes harder
    # as the natural ordering is just by time.
