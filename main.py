import os
import sys
import time
import magic
import imagehash
from PIL import Image, ExifTags


def get_image_files(path):
    """
    Check path recursively for files. If any compatible file is found, it is
    yielded with its full path.
    :param path:
    :return: yield absolute path
    """
    def is_image(file_name):
        # List mime types fully supported by Pillow
        full_supported_formats = ['gif', 'jp2', 'jpeg', 'pcx', 'png', 'tiff', 'x-ms-bmp',
                                  'x-portable-pixmap', 'x-xbitmap']
        try:
            mime = magic.from_file(file_name, mime=True)
            return mime.rsplit('/', 1)[1] in full_supported_formats
        except IndexError:
            return False

    path = os.path.abspath(path)
    for root, dirs, files in os.walk(path):
        for file in files:
            file = os.path.join(root, file)
            if is_image(file):
                yield file

def get_file_info(file):
    try:
        print(f'info: {file}')
        img = Image.open(file)

        file_size = get_file_size(file)
        image_hash = get_image_hash(img)
        image_size = get_image_size(img)
        capture_time = get_capture_time(img)

        # return file, image_hash, file_size, image_size, capture_time
        return image_hash, capture_time
    except OSError:
        return None

def get_image_hash(img):
    hashes = []
    # hash the image 4 times and rotate it by 90 degrees each time
    for angle in [ 0, 90, 180, 270 ]:
        if angle > 0:
            turned_img = img.rotate(angle, expand=True)
        else:
            turned_img = img
        hashes.append(str(imagehash.phash(turned_img)))

    return ''.join(sorted(hashes))

def get_file_size(file_name):
    try:
        return os.path.getsize(file_name)
    except FileNotFoundError:
        return 0

def get_image_size(img):
    return "{} x {}".format(*img.size)

def get_capture_time(img):
    try:
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items()
            if k in ExifTags.TAGS
        }
        return exif["DateTimeOriginal"]
    except:
        return None

def move_file(file_name, trash):
    if not os.path.exists(trash):
        os.makedirs(trash)
    try:
        os.rename(file_name, trash + os.path.basename(file_name))
        return True
    except:
        return False


#################################################

def check_dates(path):
    count = 0
    total = 0
    files = get_image_files(path)
    for file in files:
        total += 1
        image = Image.open(file)
        captured = get_capture_time(image)
        if captured == None:
            count += 1
            print(file)
    print(count,total)



def get_image_name(file, captured):

    if captured == None:
        return None

    captured = captured.replace(':', '-', 2)
    captured = captured.replace(':', '.', 2)
    directory = os.path.dirname(file)
    extension = os.path.splitext(file)[1].lower()

    name = os.path.join(directory, captured + extension)

    if name == file:
        return name

    i = 1
    while os.path.exists(name):
        name = os.path.join(directory, f"{captured}-{i}{extension}")
        i += 1

    return name 

def group_duplicates(files):
    files_info = {}
    for file in files:
        (hash, captured) = get_file_info(file)
        if hash not in files_info:
            files_info[hash] = []
        files_info[hash].append((file, captured))
    return files_info

def main(path):
    trash = path + '/trash/'
    files = get_image_files(path)
    groups = group_duplicates(files)

    for hash, files in groups.items():
        print(hash)
        files.sort(key=lambda f: (f[1] or "", f[0]))

        # Remove duplicates
        for (dup_path, dup_cap) in files[:-1]:
            print(f'trashing dup: {dup_path, dup_cap}')
            move_file(dup_path, trash)

        # Rename file
        (path, captured) = files[-1]

        new_path = get_image_name(path, captured)

        if new_path == None or new_path == path:
            print(f'skipping: {path, captured}')
        else:
            print(f'renaming: {path} -> {new_path}')
            os.rename(path, new_path)  



if __name__ == '__main__':

    # Check dates
    # check_dates(sys.argv[1])

    # Remove dups & rename
    main(sys.argv[1])


