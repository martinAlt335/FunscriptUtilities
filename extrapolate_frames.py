import json
import math
import os
import sys
import coloredlogs
import logging

# Create and start logger object.
from decord import VideoReader, cpu

from utils import pairwise

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


def extrapolate_frames(video_path):
    """
    Extrapolate actions from a funscript file. Generates a point at every frame
    by looking at the distance between two points. Uses decord's VideoReader.
    :param video_path: path of the video
    :return: count of images saved
    """


    video_dir, video_filename = os.path.split(video_path)

    assert os.path.exists(video_path)  # assert the video file exists
    try:
        assert os.path.exists(os.path.splitext(video_path)[0] + '.funscript')  # assert the associated
        logger.debug('Successfully found funscript file.')
        # funscript file exists
    except AssertionError:
        logger.error('Funscript file not found. Please make sure the funscript file'
                     ' has the same name and is in the same place as the video.')
        sys.exit(1)

    # Load the VideoReader
    # note: GPU decoding requires decord to be built from source. Uses NVIDIA codecs.
    # See https://github.com/dmlc/decord#install-via-pip. NVIDIA GPUs only.
    decoder = cpu(0)  # can set to cpu or gpu .. decoder = gpu(0)
    video = VideoReader(video_path, ctx=decoder)

    if str(decoder).split('(', 1)[0] == 'cpu':
        logger.warning('GPU processing disabled. To use your GPU for faster processing visit:'
                       ' https://github.com/dmlc/decord#install-via-pip. NVIDIA GPUs only.')

    fpms = video.get_avg_fps() / 1000  # frames per millisecond

    # Load the funscript file
    with open(os.path.splitext(video_path)[0] + '.funscript') as f:
        data = json.load(f)

    actions = data['actions']  # point to the array we require from the funscript JSON array

    for a, b in pairwise(actions):
        distance = math.floor(((b['at'] - a['at']) * fpms))  # how many frames/points can fit between two,
        # round down to prevent overshoot.
        for i in range(1, distance + 1):
            formula = ((a['pos']) + i * ((b['pos'] - a['pos']) / (distance + 1)))  # formula for finding the 'pos' key
            # for the points we wish to fit in.

            actions.append({'at': round(((a['at'] * fpms) + i) / fpms), 'pos': round(formula)})

    actions.sort(key=lambda x: x['at'])

    del data['actions']  # drop source funscript actions array
    with open(video_dir + '/' + os.path.splitext(video_filename)[0] + '_extrapolated.funscript', 'w') as fp:
        json.dump(({'actions': actions}, data), fp, indent=4)  # append new actions array to new JSON and export it.
