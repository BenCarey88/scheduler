
Unused Modules
==============

I've made a couple of bits of code that aren't really being used atm.
Just want to keep a note of them so I can get rid of them if I don't decide to
use them in the end:


Id
--
I think I want to ramp back on the use of ids overall in the code/remove
entirely. They are actively being used in the edit log to compare edits but
afaik there's no reason we can't just use == on the edits directly instead of
the ids.

Outside of that, the point of building my own Id class was meant to be to
create an id registry so that I can look up items by id. Specifically This
would allow me to change an item of one type to one of another type (eg.
Task to TaskCategory) and transfer the id from one to the other so that a
class holding a reference to that first item can hold it by id and then
knows it's now pointing to the new item.

My issue with this is it's fairly cumbersome to remember that every class
with a tree item attribute needs to store the id instead and then look up by
id. As a design pattern, I much prefer the idea that the item instance never
changes, and any edits on it just mutate the class - so this would mean
deprecating TaskCategory and Task as they exist now, and instead just having
a TaskTreeItem (or similar) class, with a new type property (need to work on
name as task type already refers to routine/general. Maybe make it tree_type
and task_type?)

Once this is done, Ids should be removable entirely. (And the id serializer
can be removed too). Inside the code, we then just work with class instances
directly.
There's still a question of how to serialize attributes to things like calendar
items (which don't have a natural path to them) and Ids could well have a place
there though, so need to think about that a bit. The serializer as it stands
should be removed anyway.


Timeline
--------

The Timeline class is meant to be a nicer container for calendar items (and
potentially other things too) - it's meant to allow more intuitive lookup
(lookup by time) and time-ordered iteration.

The thing is, I can't actually think of a use case for looking up by time, or
for time-ordered iteration - and as it stands, time-ordered iteration is
actively unhelpful because it doesn't easily allow a user to reorder the
calendar items to pick which one is on top in the calendar view.

We can definitely implement some stuff to fix that issue (though it may be
pretty inefficient, although doubt it would be inefficient enough to make any
noticable difference) but the bigger point is that I can't currently see a use
case for it.

Might be worth holding off on deleting the class for a bit though, as it could
well be useful down the line. Just need to keep an eye on it and remove if
it's clear we won't need it.
