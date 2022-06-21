"""Task Outliner Panel."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.tree import OutlinerTreeModel

from .base_tree_view import BaseTreeView


class Outliner(BaseTreeView):
    """Task Outliner panel."""
    def __init__(self, tab, tree_manager, parent=None):
        """Initialise task outliner.

        Args:
            tab (BaseTab): tab this outliner is used for.
            tree_manager (TreeManager): tree manager item.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(Outliner, self).__init__(tree_manager, parent=parent)
        self.tab = tab
        self.tree_manager = tree_manager
        self.root = tree_manager.tree_root
        self._allow_key_events = True
        self._is_full_tree = True
        self._is_outliner = True
        # TODO: get this from user prefs:
        self._hide_filtered_items = False

        self.setModel(
            OutlinerTreeModel(
                self.tree_manager,
                hide_filtered_items=self._hide_filtered_items,
                parent=self
            )
        )
        self.selectionModel().currentChanged.connect(
            self.on_current_changed
        )
        self.model().dataChanged.connect(
            self.tab.on_outliner_filter_changed
        )
        self.model().dataChanged.connect(self.on_model_data_change)

        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.header().resizeSection(1, 1)

        self.expand_items_from_tree_manager()
        self.expanded.connect(partial(self.mark_item_expanded, value=True))
        self.collapsed.connect(partial(self.mark_item_expanded, value=False))

        # self.setSelectionBehavior(
        #     QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        # )

    def _expand_item_from_tree_manager(self, index):
        """Recursively expand item at given index.

        This only expands items marked as expanded in the tree_manager.

        Args:
            index (QtCore.QModelIndex): index of item to expand.
        """
        if not index.isValid():
            return
        item = index.internalPointer()
        if item is None:
            return
        if self.tree_manager.is_expanded(item):
            self.setExpanded(index, True)
        else:
            self.setExpanded(index, False)
        for i in range(item.num_children()):
            child_index = self.model().index(i, 0, index)
            self._expand_item_from_tree_manager(child_index)

    def expand_items_from_tree_manager(self):
        """Expand all items marked as expanded in tree_manager."""
        for i in range(self.root.num_children()):
            child_index = self.model().index(i, 0, QtCore.QModelIndex())
            self._expand_item_from_tree_manager(child_index)

    def mark_item_expanded(self, index, value):
        """Mark item as expanded in tree manager.

        This is called whenever an item is collapsed/expanded in the view.

        Args:
            index (QtCore.QModelIndex): index of item.
            value (bool): whether or not the item should be expanded.
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                self.tree_manager.expand_item(item, value)

    def expand_items_from_filtered(self):
        """Expand or collapsed items based on which are filtered.

        Returns:
            (bool): whether or not action is successful.
        """
        success = self.tree_manager.set_expanded_from_filtered()
        self.expand_items_from_tree_manager()
        return success

    def toggle_items_hidden(self):
        """Toggle whether or not items are hidden.

        Returns:
            (bool): whether or not action is successful.
        """
        self._hide_filtered_items = not self._hide_filtered_items
        return self.model().set_items_hidden(self._hide_filtered_items)

    def on_current_changed(self, new_index, old_index):
        """Callback for when current index is changed.

        Args:
            new_index (QtCore.QModelIndex): new index.
            old_index (QtCore.QModelIndex): previous index.
        """
        if new_index.isValid():
            item = new_index.internalPointer()
            if item:
                self.tree_manager.set_current_item(item)
                self.tab.on_outliner_current_changed(item)

    def on_model_data_change(self, *args):
        """Update view to pick up changes in model."""
        self.viewport().update()

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()
        success = False

        if modifiers == QtCore.Qt.ControlModifier:
            # ctrl+h: hide or unhide filtered items in outliner
            if event.key() == QtCore.Qt.Key_H:
                success = self.toggle_items_hidden()
                if success:
                    self.expand_items_from_tree_manager()
            # ctrl+e: auto-collapse and expand based on filter-status
            elif event.key() == QtCore.Qt.Key_E:
                success = self.expand_items_from_filtered()

        super(Outliner, self).keyPressEvent(event)

    def _build_right_click_menu(self, item=None):
        """Build right click menu for given item.

        Args:
            item (BaseTreeItem or None): item to build menu for.

        Returns:
            (QtWidgets.QMenu): the right click menu.
        """
        right_click_menu = super(Outliner, self)._build_right_click_menu(
            item=item
        )
        right_click_menu.addSeparator()

        if self._hide_filtered_items:
            action = right_click_menu.addAction("Unhide filtered items")
        else:
            action = right_click_menu.addAction("Hide filtered items")
        self._connect_action_to_func(action, self.toggle_items_hidden)

        action = right_click_menu.addAction("Expand from filtered")
        self._connect_action_to_func(action, self.expand_items_from_filtered)

        return right_click_menu
