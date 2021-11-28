
See also design ideas file.


Directory structure
-------------------

Not sure if it makes sense for table model to be in section with other models.
Maybe we should have the main categories in the ui directory be the different
tabs, ie. 'task', 'timetable', etc. then also a 'common' or 'base' directory
for outliner, maybe a base model, base delegate, potentially also the utils and
constants

So (not sure if we need the tabs under a separate tab directory or not):

ui
    tabs
        task
            model
                ...
            widgets
                ...
        timetable
        tracker
        reviewer
        suggestions
    common
    style
    icons



Tree Manager
------------

break out using multiple inheritance:

TreeManager(FilterManager, EditManager, ...)
EditManager
FilterManager
