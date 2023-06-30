
1) new dialogs (break out into new dialog module)
    - task dialog
        - task attributes:
            - name
            - (maybe path, but uneditable)
            - display_name (defaults to name but can be changed)
            - size
            - importance
        - option to update status
        - option to track it
        - history, with edit options
        - colour editor
        - (list of planned items/scheduled items?)
    - archive manager dialog
        - side by side view with arrow buttons and drag/drop

2) update existing dialogs
    - schedule dialog and planner dialog (inherit from same class?):
        - add status option
        - add name_override option (defaults to task display_name)
        - add colour_override option (defaults to task colour)
        - add end_date option for RepeatScheduledItems
        - (add value option? probably leave this for later)
        - (list of parents and children?)
    - filter dialog
        - allow selecting groups of conditions and adding/removing from subbox
        - change the 'and/or' combobox to be in place of the 'and/or' labels

3) collapsible sidebars for outliner and filter view
    - and add into the user settings too

-------------------


