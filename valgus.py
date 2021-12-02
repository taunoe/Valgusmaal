#!/usr/bin/env python3

"""
The input is a video file.
Two modes.
Script find the lightest pixels from each frame and merges it all together into one image.

Usage:


Author:  Tauno Erik
Started: 28.11.2021
Edited:  02.12.2021
"""

# https://towardsdatascience.com/a-simple-guide-to-command-line-arguments-with-argparse-6824c30ab1c3
# https://stackoverflow.com/questions/14919609/is-this-file-a-video-python
# https://exif.readthedocs.io/en/latest/api_reference.html#image-attributes

import cv2 as cv          # pip3 install opencv-python
import numpy as np
import argparse, os, sys
import mimetypes
import exif               # pip3 install exif

# Constants
EXT = ".jpg"
LIGHT_EXT = "_light" + EXT
DARK_EXT = "_dark" + EXT
LIGHT = 0
DARK = 1
# Exif
AUTHOR = "Tauno Erik"
SOFTWARE = "valgus.py"
COMMENT = "2021"

def main(argv):
  parser = argparse.ArgumentParser()

  # Optional arguments:
  parser.add_argument("-v","--video", type=str, help="Input video file")
  parser.add_argument("-f","--folder", type=str, help="Input folder")

  args = parser.parse_args()

  if args.video:
    process_file_input(args.video)
  elif args.folder:
    process_folder_input(args.folder)
  else:
    filename = input("Insert video filename: ")
    process_file_input(filename)


def process_folder_input(foldername):
  print("Opening folder: {}".format(foldername))
  path = os.getcwd() + '/' + foldername
  files = os.scandir(path)
  for file in files:
    if file.is_file:
      file_path = foldername + "/" + file.name
      if is_video(file_path):
        print("Opening file: {}".format(file_path))
        process_video(file_path)
  files.close()


def process_file_input(filename):
  # Absolute path to input
  filepath = os.getcwd() + '/' + filename
  if os.path.isfile(filepath):
    if is_video(filepath):
      process_video(filename, LIGHT)
      process_video(filename, DARK)
    else:
      print("Not a video.")
  else:
    print("{} - is not a file!".format(filename))


def process_video(video_file, mode = LIGHT):
  if mode == LIGHT: 
    print("Processing light image...")
    EXT = LIGHT_EXT
  elif mode == DARK:
    print("Processing dark image...")
    EXT = DARK_EXT
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

  # When everything done, release the capture
  cap.release()
  # Save finalimage
  save_image(filepath, image, mode)


def save_image(filepath, image, mode):
  #
  if mode == LIGHT: 
    MODE_EXT = LIGHT_EXT
  elif mode == DARK:
    MODE_EXT = DARK_EXT
  else:
    print("Unknown mode: {}".format(mode))

  if EXT == ".jpg" or EXT == ".tiff":
    print("Adding EXIF data.")
    # Save finalimage with metadata
    # https://exif.readthedocs.io/en/latest/usage.html#writing-saving-the-image
  
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
  else: # png
    cv.imwrite(os.path.splitext(filepath)[0] + MODE_EXT, image)


def is_video(file):
  if mimetypes.guess_type(file)[0].startswith('video'):
    return True
  return False


if __name__ == "__main__":
    main(sys.argv)