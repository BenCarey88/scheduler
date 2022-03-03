"""Convert old-style tree order files to new-style ones."""

import json
import os
import sys


def convert_task_info_files_to_order_jsons(directory):
    """Convert .info txt files to .order json files in directory tree.

    Args:
        directory (str): path to directory to traverse.
    """
    for subdir, _, files in os.walk(directory):
        subdir_relpath = os.path.relpath(subdir, directory)
        if not subdir_relpath.startswith("tasks"):
            # only want to fix this for tasks
            continue
        for file in files:
            file_path = os.path.join(subdir, file)
            splt_file = os.path.splitext(file_path)
            if splt_file[1] == ".info":
                with open(file_path, "r") as file_:
                    order = [line for line in file_.read().split("\n") if line]
                new_file_path = "{0}.order".format(splt_file[0])
                if os.path.exists(new_file_path):
                    raise Exception(
                        "Order file {0} already exists".format(new_file_path)
                    )
                with open(new_file_path, "w+") as file_:
                    json.dump(order, file_, indent=4)
                print (
                    "Switching file {0} for {1}".format(
                        file_path,
                        new_file_path
                    )
                )
                os.remove(file_path)


if __name__ == "__main__":
    current_dir = sys.argv[1] if len(sys.argv) >= 2 else os.getcwd()
    current_dir = os.path.abspath(current_dir)
    print (current_dir)
    convert_task_info_files_to_order_jsons(current_dir)
