
before next release:
--------------------
* add parent_list arg to serializable from_dict
* remove title_string methods in datetime and instead change string and from_string
    methods to have identical arguments with defaults added in (eg. long=False,
    date_order="dmy", separator="-")
* add those strings to calendar_period classes in to_ and from_dict methods
* make calendar class with serialization
* calendar edits:
    - change time/day (sort continuous issue)
    - create calendar item
    - edit calendar item (inc. change day)
* link up to timetable_tab & model

* add TaskValue struct and integrate into Task class
* link up to tracker (with hardcoded values)


general:
--------
* add in loggers everywhere

