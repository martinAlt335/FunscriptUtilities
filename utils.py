import fnmatch
import itertools
import json
import os
import coloredlogs
import cv2
import imutils
import logging
import numpy as np
from decord import VideoReader
from decord import cpu

# Check OS
if os.name == 'nt':
    import win32com.client as com
    isWindows = True

# Create and start logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def extract_frames(video_path, frames_dir, overwrite=False, width=300):
    """
    Extract specified frames from a funscript video using decord's VideoReader
    :param width: width of the extracted frames saved
    :param video_path: path of the video
    :param frames_dir: the directory to save the frames
    :param overwrite: to overwrite frames that already exist?
    :return: count of images saved
    """

    saved_count = 0  # Initialize variable
    video_path = os.path.normpath(video_path)  # get path of video
    frames_dir = os.path.normpath(frames_dir)  # get folder directory of video

    video_dir, video_filename = os.path.split(video_path)  # get the video path and filename from the path

    assert os.path.exists(video_path)  # assert the video file exists
    assert os.path.exists(os.path.splitext(video_path)[0] + '.funscript')  # assert the associated funscript file exists

    # load the VideoReader
    # Note: GPU encoding requires decord to be built from source. See github readme.
    vr = VideoReader(video_path, ctx=cpu(0))  # can set to cpu or gpu .. ctx=gpu(0)

    fpms = vr.get_avg_fps() / 1000  # frames per millisecond

    # Load the funscript file
    with open(os.path.splitext(video_path)[0] + '.funscript') as f:
        data = json.load(f)

    actions = data['actions']  # Point to the array we require from the JSON array

    # Step 2: Create folders associated with the 'pos' position

    # Initialize empty array targeting the 'pos' object keys from array
    formatted_points = []
    for x in actions:
        formatted_points.append(x['pos'])

    formatted_points = np.unique(formatted_points)  # Strip array to unique points for folder creation

    for x in formatted_points:
        os.makedirs(os.path.join(frames_dir, 'output', video_filename, str(x)), exist_ok=True)

    # Step 3: Extract frames associated with the 'at' object keys from array.

    # Remove redundant actions (when no change happens between two points in the funscript file)
    for a, b in pairwise(actions):
        if a['pos'] == b['pos']:
            actions.pop(actions.index(b))  # Drop the latter action, redundant.

    for index in actions:  # loop through the funscript timestamps to the approx. frame of the video
        timestamp = (index['at'])
        vr.seek(round(fpms * timestamp))  # Round decimal to approx. frame and go to it.
        frame = vr.next()  # read the image from capture
        image_count = len(
            fnmatch.filter(os.listdir(os.path.join(frames_dir, 'output', video_filename, str(index['pos']))),
                           '*.jpg'))  # Get total files in folder and add 1 to the next image saved.
        save_path = os.path.join(frames_dir, 'output', video_filename, str(index['pos']),
                                 "{:01d}.jpg".format(image_count + 1))  # create the save path
        if not os.path.exists(save_path) or overwrite:  # if it doesn't exist or we want to overwrite anyways
            resized_image = imutils.resize(frame.asnumpy(), width)
            cv2.imwrite(save_path, cv2.cvtColor(resized_image, cv2.COLOR_RGB2BGR))  # save the extracted image
            saved_count += 1  # increment our counter by one

        # Logging overall status
        if actions.index(index) % 5 == 0:

            if isWindows:  # If Windows, can log folder size as well.
                fso = com.Dispatch('Scripting.FileSystemObject')
                folder = fso.GetFolder(os.path.join(frames_dir, 'output', video_filename))
                mb = 1024 * 1024.0
                logger.debug(f'Funscript actions processed: ' + str(actions.index(index)) + ' of ' + str(
                    len(actions)) + '. Folder size: ' + '%.2f MB' % (folder.Size / mb))
            else:
                logger.debug(f'Funscript actions processed: ' + str(actions.index(index)) + ' of ' + str(
                    len(actions)) + '.')

        # Log at every 5%
        if round(actions.index(index) / len(actions) * 100, 2) % 5 == 0:
            logger.debug(f'Status: ' + str(round(actions.index(index) / len(actions) * 100, 2)) + '%')

    return saved_count  # and return the count of the images we saved
