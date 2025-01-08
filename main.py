import os
import sys
import datetime
import imagehash
from pathlib import Path
from PIL import Image, ExifTags

class ImageInfo:
    def __init__(self, path, hash, o_time, c_time, m_time, size, dimensions):
        self.path = path
        self.hash = hash
        self.o_time = o_time
        self.c_time = c_time
        self.m_time = m_time
        self.size = size
        self.dimensions = dimensions

def is_image(path):
    try:
        with Image.open(path) as img:
            img.verify() 
            return True
    except Exception as e:
        return False

def get_image_info(path):
    with Image.open(path) as img:
        hash = get_image_hash(img)
        size = get_file_size(path)
        o_time = get_image_otime(img)
        c_time = get_file_ctime(path)
        m_time = get_file_mtime(path)
        dimensions = get_image_dimensions(img)

        return ImageInfo(path, hash, o_time, c_time, m_time, size, dimensions)

def get_image_hash(img):
    # slow, if just renaming files can skip this.
    # return '' # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    hashes = []
    for angle in [0, 90, 180, 270]:
        turned_img = img.rotate(angle, expand=True) if angle > 0 else img
        hashes.append(str(imagehash.phash(turned_img)))
    return ''.join(sorted(hashes))

def get_file_size(path):
    return os.path.getsize(path)

def get_image_dimensions(img):
    return img.size

def get_image_otime(img):
    try:
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items()
            if k in ExifTags.TAGS
        }

        # format: 2024:10:27 14:39:19
        return datetime.datetime.strptime(exif["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")

    except:
        return None
    
def get_file_ctime(path):
    return datetime.datetime.fromtimestamp(os.stat(path).st_mtime)

def get_file_mtime(path):
    return datetime.datetime.fromtimestamp(os.stat(path).st_ctime)

def progress(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    total = len(iterable)
    if total > 0: 
        # Progress Bar Printing Function
        def printProgressBar (iteration):
            percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
            filledLength = int(length * iteration // total)
            bar = fill * filledLength + '-' * (length - filledLength)
            print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Initial Call
        printProgressBar(0)
        # Update Progress Bar
        for i, item in enumerate(iterable):
            yield item
            printProgressBar(i + 1)
        # Print New Line on Complete
        print()

#################################################

def load_images(dir):
    files = [f.absolute() for f in Path(dir).iterdir() if f.is_file()]
    return [get_image_info(file) for file in progress(files) if is_image(file)]

def canonize_names(files):

    for file in files:
        # print(file.path, file.o_time, file.c_time, file.m_time)
        # continue

        src = Path(file.path)
        date = file.o_time or file.c_time
        dest = src.with_name(f"{date.strftime("%Y-%m-%d %H.%M.%S")}{src.suffix}")
        if file.path != dest: 
            print(f'Renaming {file.path} -> {dest}')
            # src.rename(dest)

def find_duplicates(files):
    # create dups destination
    dups = os.path.join(dir, 'dups')
    if not os.path.exists(dups):
        os.makedirs(dups)

    # group them by hash
    hashmap = {}
    for file in files:
        if file.hash not in hashmap:
            hashmap[file.hash] = []
        hashmap[file.hash].append(file)

    # Move duplicates to dups folder
    for hash, files in hashmap.items():
        if len(files) > 1:

            print(f'Found {len(files)} dups with hash {hash}:')

            # sort them by date
            files.sort(key=lambda f: (f.o_time or "", f.path))

            for file in files:
                print(f'{file.path}: {file.o_time} {file.size} {file.dimensions}')

            for file in files[:-1]:
                files.remove(file)
                dest = os.path.join(dups, os.path.basename(file.path))
                print(f'moving: {file.path, dest}')
                # os.rename(file.path, dest)

def main(dir):

    # get all images files in the directory
    files = load_images(dir)

    # find_duplicates(files)

    canonize_names(files)


if __name__ == '__main__':
    main(sys.argv[1])
