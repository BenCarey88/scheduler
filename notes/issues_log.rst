
Issue being hit with deserialization:

- if a task has / in it then it screws up its path so we can't get it from
    the root item. Maybe make the ui refuse to allow adding a / in? Otherwise
    might have to do some kind of internal escape character logic or something

- more generally, note that json converts None type to the string "null". This
    should be caught in deserializations

- refocus issue when renaming in task view (jumps to selected outliner category)
