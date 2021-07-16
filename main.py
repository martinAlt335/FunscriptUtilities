import os
import easygui
import coloredlogs
import logging

from extract_frames import extract_frames

# Create and start logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')


def fs_video_to_frames(video_path, width=600, remove_duplicates=True, overwrite=False, bulk_mode=False):
    """
    Extracts the frames from an associated funscript video
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

        logger.info('Processing video: {}'.format(video_filename))

        extract_frames(video_path, frames_dir, width, remove_duplicates, overwrite, bulk_mode)
        # let's now extract the frames


if __name__ == '__main__':

    # Configuration
    width = 600  # saved image width pixels
    remove_duplicates = False  # should duplicates be removed? See readme, for standard use case: true.
    overwrite = False  # should overwrite existing files? currently not adapted fully.

    video_path = easygui.fileopenbox(multiple=True)

    if len(video_path) > 1:
        fs_video_to_frames(video_path, width, remove_duplicates, overwrite, bulk_mode=True)
    else:
        fs_video_to_frames(video_path, width, remove_duplicates, overwrite,)
