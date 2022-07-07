"""Task tree model."""

from scheduler.ui import constants
from ._base_tree_model import BaseTreeModel


class ItemDialogTreeModel(BaseTreeModel):
    """Model for the full task tree."""

    def __init__(self, tree_manager, parent=None):
        """Initialise task tree model.

        Args:
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
            hide_filtered_items (bool): if True, use the child_filter from the
                tree manager to filter out all items whose checkboxes are
                deselected in the outliner.
        """
        super(ItemDialogTreeModel, self).__init__(
            tree_manager,
            mime_data_format=constants.ITEM_DIALOG_TREE_MIME_DATA_FORMAT,
            parent=parent,
        )
