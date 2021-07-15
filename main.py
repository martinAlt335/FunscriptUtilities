import os
import easygui

from extract_frames import extract_frames


def fs_video_to_frames(video_path, overwrite=False, width=600):
    """
    Extracts the frames from an associated funscript video
    :param width: Final width of the extracted frames saved.
    :param video_path: path to the video
    :param overwrite: overwrite frames if they exist?
    :return: path to the directory where the frames were saved, or None if fails
    """

    video_path = os.path.normpath(video_path)  # make the paths OS (Windows) compatible
    frames_dir = os.path.dirname(video_path)  # make the paths OS (Windows) compatible

    video_dir, video_filename = os.path.split(video_path)  # get the video path and filename from the path

    # make directory to save frames, its a sub dir in the frames_dir with the video name
    os.makedirs(os.path.join(frames_dir, 'output', video_filename), exist_ok=True)

    print("Extracting frames from {}".format(video_filename))

    extract_frames(video_path, frames_dir, overwrite, width)  # let's now extract the frames

    return os.path.join(frames_dir, video_filename)  # when done return the directory containing the frames


if __name__ == '__main__':
    bulk_load = False

    if easygui.ynbox('', 'Run in standard mode?'):
        bulk_load = False
        video_path = easygui.fileopenbox()
        fs_video_to_frames(video_path, overwrite=False, width=600)
    else:
        bulk_load = True
