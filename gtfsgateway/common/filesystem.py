import os


def clear_directory(directory):
    for f in os.listdir(directory):
        if not os.path.isdir(directory):
            continue

        os.remove(os.path.join(directory, f))