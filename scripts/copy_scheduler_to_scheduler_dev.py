"""Copy all scheduler files to scheduler dev files, EXCEPT for git."""

import os
import shutil


if __name__ == "__main__":
    scheduler_files = os.path.normpath(
        "/users/benca/OneDrive/Documents/Admin/Scheduler"
    )
    dev_scheduler_files = os.path.normpath(
        "/users/benca/OneDrive/Documents/Admin/Scheduler_dev"
    )
    for file_or_dir in os.listdir(scheduler_files):
        if file_or_dir == ".git":
            continue
        old_path = os.path.join(scheduler_files, file_or_dir)
        new_path = os.path.join(dev_scheduler_files, file_or_dir)
        if os.path.isfile(old_path):
            print ("copying file {0} to {1}".format(old_path, new_path))
            if os.path.exists(new_path):
                os.remove(new_path)
            shutil.copy2(old_path, new_path)
        elif os.path.isdir(old_path):
            print ("copying directory {0} to {1}".format(old_path, new_path))
            if os.path.exists(new_path):
                shutil.rmtree(new_path)
            shutil.copytree(old_path, new_path)
