
See also design ideas file.


Renaming Calendar Classes
-------------------------

At the moment, we use 3 very similar terms across the code base and they're
kind of doing multiple things

* Calendar
    - Used for the calendar object (provides access to day, week, month, year
        structures).
    - Also used for calendar items and the calendar tab which is where you view
        the calendar items (ie. items scheduled for a specific day).
        This is kind of confusing now because we also have planned items which
        live in the same calendar structure so arguably these have just as much
        claim to be called calendar items as the scheduled ones.
* Timetable
    - Used to refer to models/views that lay out data according in a timetable
    - Also used as a base name for all classes/tabs that make use of the
        calendar structure. This was just to avoid confusion when the word
        calendar was being used for multiple things, but really it's not a very
        accurate use of the word, and now gets confusing with the other more
        accurate use of the word timetable.
* Scheduler
    - Just the name of the app

We should change this to more intuitive uses of the words. The problem is that
I can't really think of another word outside of these 3 which I particularly
want to use (don't particularly like diary or organiser). If I can think of a
good new name for the app then I'll update this but otherwise this is what I
want to switch to:

* Calendar
    - Used for the calendar object (provides access to day, week, month, year
        structures).
    - Used as a basename for all classes/tabs that make use of this object.
    - Used for the name of the scheduled items tab specifically in the ui.
        This is a bit confusing as it conflicts with namings for things from
        the code but I can't call the tab 'Scheduler' unless I rename the app.
* Timetable
    - Used to refer to models/views that lay out data according in a timetable
* Scheduler / scheduled items
    - Used to refer to scheduled items and the scheduled items tab specifically
        within the code.
    - Used as the name of the app (hopefully only temporarily)


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

