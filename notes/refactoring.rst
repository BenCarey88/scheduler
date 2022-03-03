
See also design ideas file.



Tasks, TaskCategories and TaskGroups
-----------------------------------

At the moment we have:

* Outliner has Categories and Top-level Tasks
* Task View has tasks and subtasks

The two issues with this are:

* Conceptually, the top-level tasks in the Outliner all feel like they should
    be categories
* We could do with something similar to a task category in the task view, also
    eg. "writing"/"planning" tasks within each of the different story task
    trees are really classifications of task rather than tasks in their own
    right

To fix this:

* We can add a class called TaskGroup
* And switch all the Top-level tasks to task categories (+ refactor accordingly)

Then:

* Outliner is just Categories [actually now I probably want outliner is everything]
* Task View is Tasks and TaskGroups


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
