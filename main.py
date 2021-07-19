import os
import sys
import easygui
import coloredlogs
import logging

from extract_frames import extract_frames

# Create and start logger object.
from extrapolate_frames import extrapolate_frames

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


def action_director(video_path, width, remove_duplicates, overwrite, force_save, action_select, bulk_mode):
    """
    Routes the users requested action.
    :param remove_duplicates: Useful when building Machine Learning databases where having more frames
    covering same points are helpful in building the network. If true, actions that are next to each
    other that are the same will be removed.
    :param bulk_mode: Process multiple videos at one time, automatically enabled when more than one video is selected
    from GUI.
    :param width: Final width of the extracted frames saved.
    :param video_path: path to the video
    :param overwrite: overwrite frames if they exist?
    :return: path to the directory where the frames were saved, or None if fails
    """

    for video in video_path:
        video_path = os.path.normpath(video)  # normalise video path
        frames_dir = os.path.dirname(video_path)  # get directory path of video

        video_dir, video_filename = os.path.split(video_path)  # get the video path and filename from the path

        # make directory to save frames, its a sub dir in the frames_dir with the video name
        # In bulk mode, a single change is made: that is the save path becomes
        # output/bulk instead of output/'video_filename'
        if bulk_mode:
            os.makedirs(os.path.join(frames_dir, 'output', 'bulk'), exist_ok=True)
        else:
            os.makedirs(os.path.join(frames_dir, 'output', video_filename), exist_ok=True)

        logger.debug('Processing video: {}'.format(video_filename))

        if action_select == 'extract_frames':
            logger.debug('\n Current configuration: \n'
                         '  Exported image width: ' + str(width) + 'px'
                                                                   '\n  Remove duplicates: ' + str(remove_duplicates) +
                         '\n  Overwrite existing: ' + str(overwrite) + ' (not yet fully implemented)'
                                                                       '\n  Save whole VR image: ' + str(force_save))
            extract_frames(video_path, frames_dir, width, remove_duplicates, overwrite, force_save, bulk_mode)  # let's now extract the frames
        else:
            logger.debug('\n Current configuration: \n'
                         '  Extrapolating frames. ')
            extrapolate_frames(video_path)  # let's now extrapolate the frames


if __name__ == '__main__':

    # Configuration
    width = 1200  # saved image width pixels
    remove_duplicates = False  # should duplicates be removed? See readme, for standard use case: true.
    overwrite = False  # should overwrite existing files? currently not adapted fully.
    force_save = False  # if one wants to save the whole VR image, if VR video is detected it is split in half,
    # this is a bypass.
    # Todo: Fix overwrite function.
    action_select = 'extrapolate_frames'  # 'extract_frames' or 'extrapolate_frames'

    video_path = easygui.fileopenbox(multiple=True)

    if len(video_path) > 1:
        action_director(video_path, width, remove_duplicates, overwrite, force_save, action_select, bulk_mode=True)
    else:
        action_director(video_path, width, remove_duplicates, overwrite, force_save, action_select, bulk_mode=False)
    # except TypeError:
    #     logger.error('No video file selected, exiting.')
    #     sys.exit(1)
