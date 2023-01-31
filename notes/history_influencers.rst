
29/01/23

History Influencers
===================

The history influencer workflow is intended to allow different items in the
scheduler to influence the history of a task and to keep track of which items
are affecting an item's history at a given date or time. This allows us to eg.
mark a task as 'In Progress' or 'Completed' when a corresponding Scheduled item
is Completed, and then (crucially) to update the history and status of the task
if we move/modify/delete that scheduled item.

This page is intended to keep track of the workflow and my thoughts on it because
it's got WAY overcomplicated in my head, but in theory doesn't feel like it should
be too complex.


Require datetimes for all updates
---------------------------------

My latest thought is that we should require datetimes for any status update. I was
hoping to be able to do some status updates just at a date, or even globally (ie.
don't specify date or time). The point of this was to make things simpler when
updating statuses from the Planner or History tabs (which currently don't allow you
to specify times) or from the Task tab (which currently doesn't allow you to specify
a date or time).

However, we'll still need to be able to compare statuses set at a date with those set
at a datetime and its ambiguous how this should be done. Is a status at a date valid
from the start of that date? Or from the end? I could see cases where either felt
legit, and it was one of the major causes of issues here - it becomes much simpler
if everything can just be compared linearly. Then the logic for changing status on
the History, Planner and Tasks tabs can for now be:

    - History/Planner/Tracker:
        - if we're setting something for the current date, use current time as well
        - if setting for a past date, use the latest pos time (ie. 23:59)
        - if setting for a future date, use the earliest pos time? (ie. 00:00)
    - Task:
        - just use the current datetime for now (as we're already doing)

Then we can update this later with some ui changes to make it easier to change:

    - Planner/Tracker:
        - maybe have a small time combobox appear and allow scrolling through that,
            with the starting time of that combobx chosen as above?
    - History:
        - maybe can actually arrange the history view a bit more similarly to the
            timetable view with times along vertical axis (although less grid-like,
            can expand a bit more), then the time is determined by where you drop
            the item
        - alternatively just use same method as for Planner
    - Task:
        - similar to planner, can have combobox but this one determines date rather
            than time. Time is then picked automatically using the default times
            as described in the history/planner defaults above

Note that in this model we still want the history dict to be a nested date dict with
a time subdict, rather than just a datetime dict - this will be a lot easier than
refactoring the dict, but also will have advantages as we may still want to store
some info at date level.
