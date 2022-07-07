# """Callbacks to be used by schedule manager class."""

# from scheduler.api.edit.schedule_edit import (
#     AddScheduledItemEdit,
#     RemoveScheduledItemEdit,
#     ModifyScheduledItemEdit,
#     ModifyRepeatScheduledItemEdit,
#     ModifyRepeatScheduledItemInstanceEdit,
#     ReplaceScheduledItemEdit,
# )
# from .. _base_callbacks import BaseCallbacks


# class ScheduleCallbacks(BaseCallbacks):
#     """Class to store scheduler callbacks.

#     This is intended to be used as a singleton through the SCHEDULE_CALLBACKS
#     constant below and then accessed by schedule manager class.
#     """
#     def __init__(self):
#         """Initialize.

#         Callback args:
#             add_edits: (scheduled_item)
#             remove_edits: (scheduled_item)
#             update_edits: (old_item, new_item)
#         """
#         super(ScheduleCallbacks, self).__init__(
#             add_item_edit_classes=(
#                 AddScheduledItemEdit,
#             ),
#             remove_item_edit_classes=(
#                 RemoveScheduledItemEdit,
#             ),
#             update_item_edit_classes=(
#                 ModifyScheduledItemEdit,
#                 ModifyRepeatScheduledItemEdit,
#                 ModifyRepeatScheduledItemInstanceEdit,
#                 ReplaceScheduledItemEdit,
#             ),
#         )


# SCHEDULE_CALLBACKS = ScheduleCallbacks()
