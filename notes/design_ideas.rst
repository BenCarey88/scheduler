
Edits
-----

Just a note to remind: it is very important to the current design of edits that
the tree items do not change outside of user edits. Ie. we can't have an implementation
that clones tree items during the population of the ui as then the inverse edit will
no longer be being applied to the same item.

It may be worth trying to build in some kind of EditError that picks up if something
like this has happened, though not sure off the top of my head if that's doable.


Ui and Tree Class Hierarchy
---------------------------

At the moment, the ui to tree class hierarchy is roughly trying to do:

widget -> (model) -> tree_manager -> tree_items -> edits

But it strikes me that edits are very explicitly linked to the ui in concept: ie.
an edit is a user action, so basically any menu action or key event in qt that
alters the data structure should be an edit, and this is the only time edits should
be used. So (much as it pains me to consider this, as it would mean porting a lot
of functionality from BaseTreeItem and Task to edit classes), would it not be more
intuitive for widgets to interact directly with the edit classes? Or at least interact
with them through the model/tree manager. Something a bit more like:

        --> keyEvents/menus --> (model/tree_manager?) --> edits --\
      /                                                            v
widget  -->   [if item view]  -->   model  -->  tree_manager  --> tree_items
      \                                           ^
        -->       [else]       -------------------/

