
Adding new edits has become an annoyingly long process, so this is a checklist of
everything that needs to be done:

- Add any updates to underlying data class
- Create new edit class (usually from combination of subedits):
    - define subedits
    - set name and description
    - add callback args
- Add edit to edit_callbacks module
- Add edit to coresponding data manager class
- Call data manager function in ui
