import fnmatch
import json
import os
import sys
import coloredlogs
import cv2
import imutils
import logging
import numpy as np
import yaml
from decord import VideoReader, cpu, gpu

# Check OS
from utils import video_type

if os.name == 'nt':
    import win32com.client as com

    isWindows = True

# Create and start logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


def extract_frames(video_path, frames_dir, width, remove_duplicates, overwrite, force_save, bulk_mode):
    """
    Extract frames from an associated funscript video using decord's VideoReader
    :param remove_duplicates: Useful when building Machine Learning databases where having more frames
    covering same points are helpful in building the network. If true, actions that are next to each
    other that are the same will be removed.
    :param bulk_mode: Process multiple videos at one time, user can select multiple files from GUI.
    :param width: width of the extracted frames saved
    :param video_path: path of the video
    :param frames_dir: the directory to save the frames
    :param overwrite: to overwrite frames that already exist?
    :return: count of images saved
    """

    config = yaml.safe_load(open('settings.yml'))

    saved_count = 0  # initialize count variable
    video_path = os.path.normpath(video_path)  # get path of video
    frames_dir = os.path.normpath(frames_dir)  # get folder directory of video

    if bulk_mode:
        video_filename = str('bulk')
    else:
        video_dir, video_filename = os.path.split(video_path)

    assert os.path.exists(video_path)  # assert the video file exists
    try:
        assert os.path.exists(os.path.splitext(video_path)[0] + '.funscript')  # assert the associated
        logger.debug('Successfully found matching funscript file.')
        # funscript file exists
    except AssertionError:
        logger.error('Funscript file not found. Please make sure the funscript file'
                     ' has the same name and is in the same place as the video.')
        sys.exit(1)

    # Load the VideoReader
    # note: GPU decoding requires decord to be built from source. Uses NVIDIA codecs.
    # See https://github.com/dmlc/decord#install-via-pip. NVIDIA GPUs only.
    if config.get('VIDEO_DECODER') == 'cpu':
        logger.warning('GPU processing disabled. To use your GPU for faster processing visit:'
                       ' https://github.com/dmlc/decord#install-via-pip. NVIDIA GPUs only.')
        decoder = cpu(0)  # can set to cpu or gpu .. decoder = gpu(0)
    else:
        decoder = gpu(0)

    video = VideoReader(video_path, ctx=decoder)

    fpms = video.get_avg_fps() / 1000  # frames per millisecond

    # Load the funscript file
    with open(os.path.splitext(video_path)[0] + '.funscript') as f:
        data = json.load(f)

    actions = data['actions']  # point to the array we require from the funscript JSON array

    # Step 2: Create folders associated with the 'pos' position

    formatted_points = []  # initialize empty array targeting the 'pos' object key from array

    for x in actions:
        formatted_points.append(x['pos'])

    formatted_points = np.unique(formatted_points)  # strip array to unique points for folder creation

    for x in formatted_points:
        os.makedirs(os.path.join(frames_dir, 'output', video_filename, str(x)), exist_ok=True)  # create folders for
        # each unique 'pos'.

    # Step 3: Extract frames associated with the 'at' object key from array.

    total_actions = len(
        actions)  # initialize variable to store total actions prior to dropping for logging purposes.

    # Remove redundant actions (when no change happens between two points in the funscript file)
    # If remove_duplicates is false, bypass.

    if remove_duplicates:
        unique_actions = [actions[0]]  # for-loop responsible for finding redundant actions.

        for index in range(1, len(actions)):
            if actions[index]['pos'] == unique_actions[-1]['pos']:
                continue
            unique_actions.append(actions[index])
        logger.debug(f'' + str(total_actions) + ' actions found in the funscript file of which '
                     + str(len(unique_actions)) + ' are unique. (' + str(
            round(len(unique_actions) / total_actions * 100, 2)) + '%)')
    else:
        unique_actions = actions
        logger.warning(f'' + str(total_actions) + ' actions found in the funscript file. You are running in keep '
                                                  'duplicates mode.')

    is_video_vr = video_type(video)  # save boolean result from function
    # TODO: Possibly bypass function call all together if force_save is true. Issue:
    # from the way I see it, means adding more if statements, maybe better to keep it as-is for the sake
    # of code-legibility unless another way still delivers while being minimal.

    for index in unique_actions:  # loop through the funscript timestamps to the approx. frame of the video
        timestamp = (index['at'])
        video.seek(round(fpms * timestamp))  # round decimal to approx. frame and go to it.
        frame = video.next()  # read the image from capture
        image_count = len(
            fnmatch.filter(os.listdir(os.path.join(frames_dir, 'output', video_filename, str(index['pos']))),
                           '*.jpg'))  # get total files in relevant folder and add 1 to the next image saved.
        save_path = os.path.join(frames_dir, 'output', video_filename, str(index['pos']),
                                 "{:01d}.jpg".format(image_count + 1))  # create the save path

        if not os.path.exists(save_path) or overwrite:  # if it doesn't exist or we want to overwrite anyways
            resized_image = imutils.resize(frame.asnumpy(), width)
            if force_save or not is_video_vr:  # if video is 2D or user wants to save the whole VR image anyways
                cv2.imwrite(save_path, cv2.cvtColor(resized_image, cv2.COLOR_RGB2BGR))  # save the extracted image
            else:
                height, width = resized_image.shape[:2]
                # If VR, cut image vertically in-half and save first half.
                width_cutoff = width // 2
                s1 = resized_image[:, :width_cutoff]
                cv2.imwrite(save_path, cv2.cvtColor(s1, cv2.COLOR_RGB2BGR))
            saved_count += 1  # increment our counter by one

        # Logging overall status
        if actions.index(index) % 5 == 0:
            if isWindows:  # if Windows, can log folder size as well.
                fso = com.Dispatch('Scripting.FileSystemObject')
                folder = fso.GetFolder(os.path.join(frames_dir, 'output', video_filename))
                mb = 1024 * 1024.0
                logger.debug(f'Actions processed: ' + str(actions.index(index)) + ' of ' + str(
                    len(unique_actions)) + '. Folder size: ' + '%.2f MB' % (folder.Size / mb))
            else:
                logger.debug(f'Actions processed: ' + str(actions.index(index)) + ' of ' + str(
                    len(unique_actions)) + '.')

        # Log at every 5%.
        if actions.index(index) > 0 and round(actions.index(index) / len(unique_actions) * 100, 2) % 5 == 0:
            logger.debug(f'Status: ' + str(round(actions.index(index) / len(unique_actions) * 100, 2)) + '%')

    logger.debug(f'Finished successfully. ' + str(saved_count) + ' images saved.')
    return saved_count  # and return the count of the images we saved
