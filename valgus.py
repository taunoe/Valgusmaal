#!/usr/bin/env python3

"""
Python3 script to create long exposure images from videos.

Input is a video file or folder with videos.
Preferably short video: a few seconds long to get a good result.

The script generates two files: one contains the lightest pixels
and the other darkest pixels from video.

Author:  Tauno Erik
Started: 28.11.2021
Edited:  12.12.2021
"""

# https://towardsdatascience.com/a-simple-guide-to-command-line-arguments-with-argparse-6824c30ab1c3
# https://stackoverflow.com/questions/14919609/is-this-file-a-video-python
# https://exif.readthedocs.io/en/latest/api_reference.html#image-attributes
# https://exif.readthedocs.io/en/latest/usage.html#writing-saving-the-image
# https://www.tutorialkart.com/opencv/python/opencv-python-resize-image/
# https://geekflare.com/learn-python-subprocess/


import cv2 as cv          # pip3 install opencv-python
import numpy as np
import argparse, os, sys
import mimetypes
import exif               # pip3 install exif
import timeit
import threading

# Constants
EXT = ".jpg"              # Output image extentsion (jpg, png)
LIGHT = 0
DARK = 1

# Exif data
AUTHOR = "Tauno Erik"
SOFTWARE = "valgus.py"
COMMENT = "github.com/taunoe/Valgusmaal"


def is_video(file):
  '''
  Returns: True or False
  '''
  if mimetypes.guess_type(file)[0].startswith('video'):
    return True
  return False


def calculate_new_size(old_width, old_height, new_shorter_side):
    '''
    Calculates new image size.
    Returns: width, height
    '''
    # Portrait
    if old_width < old_height: 
        new_height = int((((new_shorter_side * 100) / old_width) / 100) * old_height)
        return(new_shorter_side, new_height)
    # Landscape 
    elif old_height < old_width: 
        new_width = int((((new_shorter_side * 100) / old_height) / 100) * old_width)
        return(new_width, new_shorter_side)
    # Square
    else:
        return(new_shorter_side, new_shorter_side)


def resize_image(image, new_size=1024):
  '''
  new_size: image longer side
  Returns: resized image
  '''
  width = image.shape[1]
  height = image.shape[0]
  print('Original Dimensions: ', image.shape)

  new_width, new_height = calculate_new_size(width, height, new_size)
  resized = cv.resize(image, (new_width, new_height), interpolation = cv.INTER_AREA)
  print('Resized Dimensions: ', resized.shape)

  return resized


def get_ext(mode):
  MODE_EXT = '.jpg'
  if mode == LIGHT: # == 0
    MODE_EXT = "_light" + EXT  # Light output image suffix
  elif mode == DARK: # == 1
    MODE_EXT = "_dark" + EXT    # Dark output image suffix
  else:
    print("Unknown mode: {}".format(mode))
  return MODE_EXT


def save_image(filepath, image, mode):
  '''
  mode: LIGHT==1 or DARK==0
  '''
  MODE_EXT = get_ext(mode)

  if EXT == ".jpg" or EXT == ".tiff":
    print("Adding EXIF data.")
    # Decode
    status, img_coded = cv.imencode(EXT, image)
    # To byte string
    img_bytes = img_coded.tobytes()
    # Using the exif format to add information
    exif_img = exif.Image(img_bytes)
    # Adding information
    exif_img["artist"] = AUTHOR
    exif_img["copyright"] = AUTHOR
    exif_img["software"] = SOFTWARE
    exif_img["user_comment"] = COMMENT
    # Save final image
    with open(os.path.splitext(filepath)[0] + MODE_EXT, 'wb') as img_file:
      img_file.write(exif_img.get_file())
  else: # png, no EXIF data
    cv.imwrite(os.path.splitext(filepath)[0] + MODE_EXT, image)


def process_video(video_file, mode = LIGHT, resize=False, size=1024):
  '''
  mode: LIGHT or DARK
  '''
  if mode == LIGHT: 
    print("Processing light image...")
  elif mode == DARK:
    print("Processing dark image...")
  else:
    print("Unknown mode ...")

  # Absolute path to video file
  filepath = os.getcwd() + '/' + video_file

  cap = cv.VideoCapture(video_file)
  # First frame as base image
  ret, image = cap.read()

  while (cap.isOpened()):
    ret, frame = cap.read()
    if ret:
      if mode == LIGHT: 
        image = np.maximum(frame, image)
      elif mode == DARK:
        image = np.minimum(frame, image)
    else:
      print("... Done. Saving image.")
      break
  cap.release()

  if resize == True:
    downscaled_img = resize_image(image, new_size=size)
    save_image(filepath, downscaled_img, mode)
  else:
    save_image(filepath, image, mode)

  return 0


def process_file_input(filename, resize=False, size=0):
  filepath = os.getcwd() + '/' + filename  # Absolute path to input

  if os.path.isfile(filepath):
    if is_video(filepath):
      threads = list()

      for mode in range(2):
        x = threading.Thread(target=process_video(filepath, mode, resize, size), args=(mode,))
        threads.append(x)
        x.start()

      for th in threads:
        th.join()
    else:
      print("Not a video!")
  else:
    print("{} - is not a file!".format(filename))


def process_folder_input(foldername, resize=False, size=0):
  '''
  Searches for video files in a folder.
  Ignores others.
  '''
  print("Opening folder: {}".format(foldername))
  path = os.getcwd() + '/' + foldername
  files = os.scandir(path)

  threads = list()

  for file in files:
    if file.is_file:
      filepath = foldername + "/" + file.name
      if is_video(filepath):
        print("Opening file: {}".format(filepath))

        for mode in range(2):
          x = threading.Thread(target=process_video(filepath, mode, resize, size), args=(mode,))
          threads.append(x)
          x.start()

  for th in threads:
    th.join()

  files.close()


def main(argv):
  parser = argparse.ArgumentParser()

  # Optional arguments:
  parser.add_argument("-v","--video", type=str, help="Input video file.")
  parser.add_argument("-f","--folder", type=str, help="Input folder.")
  parser.add_argument("-r","--resize", type=int, help="Output images size.")

  args = parser.parse_args()

  if args.resize:
    resize = True
    size = int(args.resize)
  else:
    resize = False
    size = 0

  if args.video:
    process_file_input(args.video, resize, size)
  elif args.folder:
    process_folder_input(args.folder, resize, size)
  else:
    filename = input("Insert video filename: ")
    process_file_input(filename, resize, size)  # Does not resize


if __name__ == "__main__":
  start_time = timeit.default_timer()

  main(sys.argv)

  print("Execution time:")
  print(timeit.default_timer() - start_time)