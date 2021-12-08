#!/usr/bin/env python3

"""
The input is a video file.
Two modes.
Script find the lightest pixels from each frame and merges it all together into one image.

Usage:


Author:  Tauno Erik
Started: 28.11.2021
Edited:  08.12.2021

TODO:
 - resize images
"""

# https://towardsdatascience.com/a-simple-guide-to-command-line-arguments-with-argparse-6824c30ab1c3
# https://stackoverflow.com/questions/14919609/is-this-file-a-video-python
# https://exif.readthedocs.io/en/latest/api_reference.html#image-attributes
# https://exif.readthedocs.io/en/latest/usage.html#writing-saving-the-image
# https://www.tutorialkart.com/opencv/python/opencv-python-resize-image/


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
COMMENT = "github.com/taunoe/Valgusmaal"

def main(argv):
  parser = argparse.ArgumentParser()

  # Optional arguments:
  parser.add_argument("-v","--video", type=str, help="Input video file.")
  parser.add_argument("-f","--folder", type=str, help="Input folder.")
  parser.add_argument("-r","--resize", type=str, help="Resize output images.")

  args = parser.parse_args()

  if args.resize:
    resize = True
    size = int(args.resize)
  else:
    # Do not resize
    resize = False
    size = 0

  if args.video:
    process_file_input(args.video, resize, size)
  elif args.folder:
    process_folder_input(args.folder, resize, size)
  else:
    filename = input("Insert video filename: ")
    process_file_input(filename, resize, size)


def process_folder_input(foldername, resize=False, size=0):
  print("Opening folder: {}".format(foldername))
  path = os.getcwd() + '/' + foldername
  files = os.scandir(path)
  for file in files:
    if file.is_file:
      file_path = foldername + "/" + file.name
      if is_video(file_path):
        print("Opening file: {}".format(file_path))
        process_video(file_path, LIGHT, resize, size)
        process_video(file_path, DARK, resize, size)
  files.close()


def process_file_input(filename, resize=False, size=0):
  # Absolute path to input
  filepath = os.getcwd() + '/' + filename
  if os.path.isfile(filepath):
    if is_video(filepath):
      process_video(filename, LIGHT, resize, size)
      process_video(filename, DARK, resize, size)
    else:
      print("Not a video.")
  else:
    print("{} - is not a file!".format(filename))


def process_video(video_file, mode = LIGHT, resize=False, size=1024):
  ''' '''
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

  # Resize image:
  if resize == True:
    downscaled_img = resize_image(image, new_size=size)
    save_image(filepath, downscaled_img, mode)
  else:
    # Save original size
    save_image(filepath, image, mode)


def resize_image(image, new_size=1024):
  '''
  new_size - is image longer side
  '''
  width = image.shape[1]
  height = image.shape[0]
  print('Original Dimensions : ', image.shape)

  new_width, new_height = calculate_new_size(width, height, new_size)

  resized = cv.resize(image, (new_width, new_height), interpolation = cv.INTER_AREA)
  print('Resized Dimensions : ', resized.shape)

  return resized


def calculate_new_size(old_width, old_height, new_shorter_side):
    '''
    Calculates new image size
    '''
    # portrait
    if old_width < old_height: 
        new_height = int((((new_shorter_side * 100) / old_width) / 100) * old_height)
        return(new_shorter_side, new_height)
    # landscape 
    elif old_height < old_width: 
        new_width = int((((new_shorter_side * 100) / old_height) / 100) * old_width)
        return(new_width, new_shorter_side)
    # square
    else:
        return(new_shorter_side, new_shorter_side)


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