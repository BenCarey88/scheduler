
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

