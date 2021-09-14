import json
import math
import os
import sys
import coloredlogs
import logging
import yaml

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

    config = yaml.safe_load(open('settings.yml'))

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

    source_actions_count = len(actions)

    for a, b in pairwise(actions[:len(actions)]):
        distance = ((b['at'] - a['at']) * fpms)  # how many frames can fit between two points,
        # round down to prevent overshoot.
        distance = math.floor(distance * (config.get('USE_PERCENTAGE')/100))  # use x% of the total frame gap between each point.

        for i in range(1, distance):
            formula = ((a['pos']) + i * ((b['pos'] - a['pos']) / distance))  # formula for finding the 'pos' key
            # for the points we wish to fit in.

            actions.append({'at': round(((a['at'] * fpms) + i) / fpms), 'pos': round(formula)})

    actions.sort(key=lambda x: x['at'])

    extrapolated_actions_count = len(actions)

    del data['actions']  # drop source funscript actions array

    # Write data to file. TODO: See if better way to JSON dump array and object. Having them together treats it as an
    #  array w/ two objects which is not what we are after. At the moment, a hacky workaround is in place.

    with open(video_dir + '/' + os.path.splitext(video_filename)[0] + '_extrapolated.funscript', 'w') as fp:
        # dump both separately until a way to dump in the way we require.
        json.dump(({'actions': actions}), fp)  # append new actions array to new JSON and export it.
        json.dump(data, fp)  # append old JSON data attributes such as 'creator' back.
    fp.close()  # close file
    f.close()  # close file

    #  Dirty fix to format extrapolated JSON file correctly.

    with open(video_dir + '/' + os.path.splitext(video_filename)[0] + '_extrapolated.funscript') as f:
        new_text = f.read().replace('}{', ',')
    f.close()

    with open(video_dir + '/' + os.path.splitext(video_filename)[0] + '_extrapolated.funscript', 'w') as f:
        f.write(new_text)
    f.close()

    logger.debug('Extrapolated frames. (' + str(round((extrapolated_actions_count/source_actions_count * 100) - 100, 2)) + '% increase) Original funscript file had ' + str(source_actions_count) + ' actions. New count: ' + str(extrapolated_actions_count) + ' actions')
