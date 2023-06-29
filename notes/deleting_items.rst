
Deleting items is a bit of an open question atm, ie. what should happen.
Eg. When we delete a task, do we want:
    1) any planned items for that task to be deleted?
    2) any scheduled items for that task to be deleted?
    3) any tracked items for that task to be deleted?
    4) all history for that task to be deleted?

If we want everything to be deleted, the best way to do this I think is
to add a RemoveFromHostEdit into the edit that deletes it, and then all
lists/dict that contain those tasks or contain tracker/planner/scheduled
items referencing those tasks can be filtered before being used (maybe even
make a list subclass to automatically do this).
    --> the list subclass might be a nice idea regardless - allows us to
        access items from the list by item.value as well so that we can
        store lists of MutableAttributes without needing annoying extra
        properties to maintain them. ALTHOUGH we also need to edit those
        lists so that may screw us over there. Unless we add a context
        manager or something to allow us to access the list normally When
        editing?

If we don't want to delete them, the main issue is that while I think most
logic would hold within a session, if the task is deleted then everything
that references it will be saved as referencing an invalid path, which
means it will be useless in future sessions.

Hence, I think if a task is deleted and is being used elsewhere (at least
in planner/scheduler/tracker - maybe history is different), we should get
a dialog saying where it's used and offering (some of?) the following options:
    - delete all items referencing this task, and all history of task
    - delete task+history and switch all referencing items to events
        - would need event equivalent for planned item in that case 
    - archive this task (so can still be referenced and see history)
    - archive this task and all items referencing it
    - archive but also delete all FUTURE items referencing task (and remove
        from tracker)
