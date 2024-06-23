import os
import zipfile


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

def create_zip_file(src, destination_zip_filename):
    with zipfile.ZipFile(destination_zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(src):
            for file in files:
                if not file.endswith('.zip'):
                    zip_file.write(
                        os.path.join(root, file),
                        os.path.basename(file)
                    )