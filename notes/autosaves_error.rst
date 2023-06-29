
Currently disablling autosaves because it's occasionally causing this error:
============================================================================

(need to investigate and then reenable)


Traceback (most recent call last):
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 806, in move
    os.rename(src, real_dst)
PermissionError: [WinError 5] Access is denied: 'C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\_autosaves\\calendar' -> 'C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\_autosaves\\tmpsfjf16h4calendar_backup_\\calendar'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\PythonPath\my-pkgs\scheduler\ui\application.py", line 240, in timerEvent
    self._autosave()
  File "C:\PythonPath\my-pkgs\scheduler\ui\application.py", line 231, in _autosave
    self.project.autosave()
  File "C:\PythonPath\my-pkgs\scheduler\api\project.py", line 468, in autosave
    self._write_all_components(self._autosaves_tree)
  File "C:\PythonPath\my-pkgs\scheduler\api\project.py", line 418, in _write_all_components
    self._calendar.write(project_tree.calendar_directory)
  File "C:\PythonPath\my-pkgs\scheduler\api\serialization\serializable.py", line 337, in write
    self.to_directory(path)
  File "C:\PythonPath\my-pkgs\scheduler\api\serialization\serializable.py", line 684, in to_directory
    self._dict_to_directory(directory_path, dict_repr)
  File "C:\PythonPath\my-pkgs\scheduler\api\serialization\serializable.py", line 620, in _dict_to_directory
    shutil.move(directory_path, tmp_dir)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 824, in move
    rmtree(src)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 740, in rmtree
    return _rmtree_unsafe(path, onerror)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 613, in _rmtree_unsafe
    _rmtree_unsafe(fullname, onerror)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 613, in _rmtree_unsafe
    _rmtree_unsafe(fullname, onerror)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 613, in _rmtree_unsafe
    _rmtree_unsafe(fullname, onerror)
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 618, in _rmtree_unsafe
    onerror(os.unlink, fullname, sys.exc_info())
  File "C:\Users\benca\AppData\Local\Programs\Python\Python39\lib\shutil.py", line 616, in _rmtree_unsafe
    os.unlink(fullname)
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\_autosaves\\calendar\\2022\\January\\2022-01-03 to 2022-01-09\\week.order'