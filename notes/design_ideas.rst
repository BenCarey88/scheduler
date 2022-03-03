
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

(PROBABLY SCRAP THIS PLAN)

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


Ui Specific Edits
-----------------

We will eventually want a way to change the state of the ui along with undo/redo in
order to show the user which edit is being changed (eg. if the last edit was on a
different tab, undo should switch to that tab). Assuming we don't want filters to
just be treated like standard edits (which is maybe an open question? But for now
I'd say it's fine without), then I believe the following are the ui state changes
we'd want to capture:

  - current tab (and current outliner tab, when these exist)
  - filtered items
  - scroll position on tab

To handle this I propose each edit can hold its own ui_state_edit_log, which holds
all ui state changes that were made after this edit was made and before the next
edit was made:

  - we also hold a temporary ui_state_edit_log in the main EDIT_LOG to hold changes
      that are made before a new edit is made, or before an undo/redo
  - pass an optional arg to all edits, so that edits have the option of being registered
    to the EDIT_LOG's ui_state_edit_log rather than the default EDIT_LOG
  - each filter change and other ui state change triggers an edit which is registered
      to the EDIT_LOG ui_state_edit_log
  - when a new edit is registered to EDIT_LOG, the temporary EDIT_LOG ui_state_edit_log
      gets set as the PREVIOUS latest edit's ui_state_edit_log attr (if there is a previous
      edit), and the EDIT_LOG ui_state_edit_log gets reset
  - calling undo on edit_A will first undo all edits in the EDIT_LOG ui_state_edit_log
      and then undo all edits in edit_A's ui_state_edit_log (the latter should only
      be nonempty on the current edit_A if some undoing has been done in the past), and
      THEN undo the edit_A itself. This should leave us in exactly the state we were in
      just before edit_A was made.
      Then the EDIT_LOG ui_state_edit_log will be reset
  - calling redo will first ENDO the EDIT_LOG ui_state_edit_log, then REDO any edits in
      the PREVIOUS latest edit's (if one exists) ui_state_edit_log THAT HAVE PREVIOUSLY
      BEEN UNDONE (if I'm not mistaken, for there to be ui_state_edits here that have been
      undone, we need to have run undo at least twice previously - the first will just
      have undone and then wiped the EDIT_LOG ui_state_edit_log, but the second will be
      applied to an edit that may actually have a ui_state_edit_log and so the ui state
      changes in this will have been undone). This should leave us in exactly the state we
      were in just after edit_A was made.
      OR: do we want to reset to the point just before edit_A was last undone? In which
      case we want to redo the ui_state_edit_log of edit_A rather than of the previous
      edit. Note that if that's what we want to do, we may well decide we need to add
      temporary ui state changes to an edit after an undo, but that becomes tricky if
      there's both a redo pending and new temporary state changes when an undo is called.
      Then the EDIT_LOG ui_state_edit_log will be reset

NOTE:
  these edits may need to be handled slightly differently in some cases: eg. the tab change
  and scroll actions are just doable by the user directly in the ui, so when a user calls
  them the edit needs to just register that action rather than trigger the action. But
  the edit still needs the ability to do/undo the action itself for redo/undo functionality.

  Note that we probably also want to inherit from actual edit classes for this though
  rather than make a new class entirely, as I'm pretty sure the filter ones could benefit
  from OrderedDictEdits
