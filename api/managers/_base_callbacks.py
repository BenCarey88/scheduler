# """Class for managing edit callbacks."""


# from scheduler.api.edit import edit_log


# class BaseCallbacks(object):
#     """Class to store callbacks.

#     Note that the implementations of the registry functions here depend
#     on the way that the edit and undo callback args are set up in the
#     relevant edit classes (eg. that the add edit callback args are the
#     same as the remove undo callback args). Any edit classes with logic
#     that doesn't match this will require different implementations in the
#     correspding callback subclass.
#     """
#     def __init__(
#             self,
#             add_item_edit_classes,
#             remove_item_edit_classes,
#             update_item_edit_classes,
#             move_item_edit_classes=None,
#             full_update_edit_classes=None):
#         """Initialize.

#         Args:
#             add_item_edit_classes (tuple(class)): list of edit classes that
#                 add the items this manager manages.
#             remove_item_edit_classes (tuple(class)): list of edit classes that
#                 remove the items this manager manages.
#             update_item_edit_classes (tuple(class)): list of edit classes that
#                 update the items this manager manages.
#             move_item_edit_classes (tuple(class) or None): list of edit classes
#                 that move the items this manager manages (if used).
#             full_update_edit_classes (tuple(class) or None): list of edit
#                 classes that require a full update (if used).
#         """
#         self._add_item_edit_classes = add_item_edit_classes
#         self._remove_item_edit_classes = remove_item_edit_classes
#         self._update_item_edit_classes = update_item_edit_classes
#         self._move_item_edit_classes = move_item_edit_classes or ()
#         self._full_update_edit_classes = full_update_edit_classes or ()

#     def _modify_callback(self, callback):
#         """Modify a callback before registering it.

#         Args:
#             callback (function): callback to modify.

#         Returns:
#             (function): modified callback.
#         """
#         return callback

#     ### Register Callbacks ###
#     def register_pre_item_added_callback(self, id, callback):
#         """Register pre item added callback.

#         Note that this implementation requires that the remove undo and the
#         add redo callbacks take in the same arguments.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): callback to run before an item is added.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._add_item_edit_classes:
#             edit_class.register_pre_edit_callback(id, callback)
#         for edit_class in self._remove_item_edit_classes:
#             edit_class.register_pre_undo_callback(id, callback)

#     def register_item_added_callback(self, id, callback):
#         """Register item added callback.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): callback to run when an item is added. This
#                 should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._add_item_edit_classes:
#             edit_class.register_post_edit_callback(id, callback)
#         for edit_class in self._remove_item_edit_classes:
#             edit_class.register_post_undo_callback(id, callback)

#     def register_pre_item_removed_callback(self, id, callback):
#         """Register callback to use before an item is removed.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call before an item is removed.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._remove_item_edit_classes:
#             edit_class.register_pre_edit_callback(id, callback)
#         for edit_class in self._add_item_edit_classes:
#             edit_class.register_pre_undo_callback(id, callback)

#     def register_item_removed_callback(self, id, callback):
#         """Register callback to use when an item is removed.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call when an item is removed.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._remove_item_edit_classes:
#             edit_class.register_post_edit_callback(id, callback)
#         for edit_class in self._add_item_edit_classes:
#             edit_class.register_post_undo_callback(id, callback)

#     def register_pre_item_moved_callback(self, id, callback):
#         """Register callback to use before an item is moved.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call before an item is moved.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._move_item_edit_classes:
#             edit_class.register_pre_edit_callback(id, callback)
#             edit_class.register_pre_undo_callback(id, callback)

#     def register_item_moved_callback(self, id, callback):
#         """Register callback to use when an item is moved.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call when an item is moved.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._move_item_edit_classes:
#             edit_class.register_post_edit_callback(id, callback)
#             edit_class.register_post_undo_callback(id, callback)

#     def register_pre_item_modified_callback(self, id, callback):
#         """Register callback to use before an item is modified.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call before an item is modified.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._update_item_edit_classes:
#             edit_class.register_pre_edit_callback(id, callback)
#             edit_class.register_pre_undo_callback(id, callback)

#     def register_item_modified_callback(self, id, callback):
#         """Register callback to use when an item is modified.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call when an item is modified.
#                 This should accept arguments specified in the run func below.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._update_item_edit_classes:
#             edit_class.register_post_edit_callback(id, callback)
#             edit_class.register_post_undo_callback(id, callback)

#     def register_pre_full_update_callback(self, id, callback):
#         """Register callback to use before the underlying data is updated.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call before the update.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._full_update_edit_classes:
#             edit_class.register_pre_edit_callback(id, callback)
#             edit_class.register_pre_undo_callback(id, callback)

#     def register_full_update_callback(self, id, callback):
#         """Register callback to use when the underlying data is updated.

#         Args:
#             id (variant): id to register callback at. Generally this will
#                 be the ui class that defines the callback.
#             callback (function): function to call before the update.
#         """
#         callback = self._modify_callback(callback)
#         for edit_class in self._full_update_edit_classes:
#             edit_class.register_post_edit_callback(id, callback)
#             edit_class.register_post_undo_callback(id, callback)

#     ### Remove Callbacks ##
#     def remove_callbacks(self, id):
#         """Remove all callbacks registered with given id.

#         Args:
#             id (variant): id to remove callbacks for.
#         """
#         edit_log.remove_edit_callbacks(id)
