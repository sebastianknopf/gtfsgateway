import os


def clear_directory(directory):
    for f in os.listdir(directory):
        if not os.path.isdir(directory):
            continue

        os.remove(os.path.join(directory, f))

def copy_file(src, dest):
    with open(src, 'rb') as src_file:
        with open(dest, 'wb') as dest_file:
            dest_file.write(src_file.read())
            dest_file.close()

        src_file.close()