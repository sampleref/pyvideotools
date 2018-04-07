import logging
import os
import shutil
from pathlib import Path

import av
import cv2
import imageio
from moviepy.editor import VideoFileClip, concatenate_videoclips

THUMB_SIZE = 320
THUMB_FRAMES = 10
VIDEO_EXT = '.mp4'
GIF_EXT = '.gif'

USER = 'user'


def main():
    logging.basicConfig(level=logging.INFO)
    # logging.info("Checking RTSP URL Result %r ", check_rtsp_url("rtsp://<host_name>:9990/test.mp4"))
    create_mp4_thumbnail("/home/" + USER + "/NAS/testvideo720paudio.mp4")
    #attach_clips(["/home/" + USER + "/NAS/testvideo720paudio.mp4", "/home/" + USER + "/NAS/test1_good.mp4", ],
     #            "/home/" + USER + "/NAS/attached.mp4")


def attach_clips(file_clips, target_file):
    logging.info("Creating attach_clips for %s ", target_file)
    file_clip_arr = list
    for file_clip in file_clips:
        if check_valid_file(file_clip):
            logging.info("attach_clips adding clip %s ", file_clip)
            file_clip_arr.append(VideoFileClip(file_clip))
        else:
            logging.error("attach_clips invalid clip %s ", file_clip)
    result_clip = concatenate_videoclips(file_clip_arr)
    remove_file_if_exists(target_file)
    result_clip.write_videofile(target_file)
    return


def check_rtsp_url(rtsp_url):
    logging.info("Checking RTSP Url %s ", rtsp_url)
    capture = cv2.VideoCapture()
    capture.open(rtsp_url)
    if capture.isOpened():
        logging.info("RTSP Url %s Works ", rtsp_url)
        is_valid = True
    else:
        logging.info("RTSP Url %s Not Working ", rtsp_url)
        is_valid = False
    capture.release()
    return is_valid


def create_mp4_thumbnail_av(video_path):
    logging.info("Creating thumbnail for %s ", video_path)

    if check_valid_file(video_path, VIDEO_EXT):
        """Extract frames from the video and creates thumbnails for one of each"""
        logging.info("Extract frames from video %s ", video_path)
        frames_path = video_to_frames_av(video_path)
        thumb_video = thumbs_to_gif(video_path, frames_path)
        if check_valid_file(thumb_video, GIF_EXT):
            logging.info("Thumbnail for %s created as %s ", video_path, thumb_video)
            remove_folder_if_exists(frames_path)
            logging.info("Removed temporary thumbs path for %s created as %s ", video_path, frames_path)
            return thumb_video
        else:
            logging.error("Thumbnail for %s cannot be created ", video_path)
    else:
        logging.error("No valid file at %s ", video_path)
    return ""


def create_mp4_thumbnail(video_path):
    logging.info("Creating thumbnail for %s ", video_path)

    if check_valid_file(video_path, VIDEO_EXT):
        """Extract frames from the video and creates thumbnails for one of each"""
        logging.info("Extract frames from video %s ", video_path)
        # Extract frames from video
        frames = video_to_frames(video_path)
        if len(frames) > 0:
            logging.info("Generate and save thumbs for %s ", video_path)
            file_name_wo_suffix = get_string_strip_suffix(video_path, VIDEO_EXT)
            logging.info("thumbs path for %s is %s _frames ", video_path, file_name_wo_suffix)
            frames_path = file_name_wo_suffix + '_frames'
            remove_folder_if_exists(frames_path)
            os.makedirs(frames_path)
            for i in range(len(frames)):
                # Generate and save thumbs
                thumb = image_to_thumbs(frames[i])
                for k, v in thumb.items():
                    cv2.imwrite(frames_path + '/%d_%s.png' % (i, k), v)
            # Create .mp4, gif from thumbs
            remove_file_if_exists(file_name_wo_suffix + '_thumbnail' + VIDEO_EXT)
            remove_file_if_exists(file_name_wo_suffix + '_thumbnail' + GIF_EXT)
            thumb_video = thumbs_to_gif(video_path, frames_path)
            if check_valid_file(thumb_video, GIF_EXT):
                logging.info("Thumbnail for %s created as %s ", video_path, thumb_video)
                #remove_folder_if_exists(frames_path)
                logging.info("Removed temporary thumbs path for %s created as %s ", video_path, frames_path)
                return thumb_video
            else:
                logging.error("Thumbnail for %s cannot be created ", video_path)
        else:
            logging.error("Frames cannot be created for %s ", video_path)
    else:
        logging.error("No valid file at %s ", video_path)
    return ""


def thumbs_to_gif(video_path, thumbs_path):
    file_name_wo_suffix = get_string_strip_suffix(video_path, VIDEO_EXT)
    thumb_gif_path = file_name_wo_suffix + '_thumbnail' + GIF_EXT
    images = []
    index = 0
    while index < THUMB_FRAMES:
        images.append(imageio.imread(thumbs_path + '/' + str(index) + '_' + str(THUMB_SIZE) + '.png'))
        index += 1
    imageio.mimsave(thumb_gif_path, images)
    return thumb_gif_path


def thumbs_to_video_av(video_path, thumbs_path):
    file_name_wo_suffix = get_string_strip_suffix(video_path, VIDEO_EXT)
    thumb_image = cv2.imread(thumbs_path + '/0_' + str(THUMB_SIZE) + '.png')
    height, width, layers = thumb_image.shape
    thumb_video_path = file_name_wo_suffix + '_thumbnail' + VIDEO_EXT

    output = av.open(thumb_video_path, 'w')
    stream = output.add_stream('mpeg4', 1)
    stream.bit_rate = 50000
    stream.pix_fmt = 'yuv420p'
    stream.height = height
    stream.width = width

    frame = av.VideoFrame.from_ndarray(thumb_image, format='bgr24')
    packet = stream.encode(frame)
    output.mux(packet)

    index = 1
    while index < THUMB_FRAMES:
        thumb_img = cv2.imread(thumbs_path + '/' + str(index) + '_' + str(THUMB_SIZE) + '.png')
        frame = av.VideoFrame.from_ndarray(thumb_img, format='bgr24')
        packet = stream.encode(frame)
        output.mux(packet)
        index += 1

    output.close()
    return thumb_video_path


def thumbs_to_video(video_path, thumbs_path):
    file_name_wo_suffix = get_string_strip_suffix(video_path, VIDEO_EXT)
    thumb_image = cv2.imread(thumbs_path + '/0_' + str(THUMB_SIZE) + '.png')
    height, width, layers = thumb_image.shape
    thumb_video_path = file_name_wo_suffix + '_thumbnail' + VIDEO_EXT
    thumb_video = cv2.VideoWriter(thumb_video_path, cv2.VideoWriter_fourcc(*'MP4V'), 1, (width, height))
    thumb_video.write(thumb_image)
    index = 1
    while index < THUMB_FRAMES:
        thumb_img = cv2.imread(thumbs_path + '/' + str(index) + '_' + str(THUMB_SIZE) + '.png')
        thumb_video.write(thumb_img)
        index += 1
    thumb_video.release()
    return thumb_video_path


def video_to_frames_av(video_filename):
    logging.info("video_to_frames_av for video %s ", video_filename)
    file_name_wo_suffix = get_string_strip_suffix(video_filename, VIDEO_EXT)
    frames_path = file_name_wo_suffix + '_frames'
    container = av.open(video_filename)
    for i, frame in enumerate(container.decode(video=0)):
        frame.to_image().save(frames_path + '/%d_320.png' % 1)
        if i > 9:
            break
    return frames_path


def video_to_frames(video_filename):
    """Extract frames from video"""
    logging.info("video_to_frames for video %s ", video_filename)
    cap = cv2.VideoCapture(video_filename)
    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    frames = []
    logging.info("video_to_frames video length %d for video %s ", video_length, video_filename)
    if cap.isOpened() and video_length > 0:
        frame_ids = [0]
        if video_length >= 4:
            frame_ids = [5,
                         round(video_length * 0.025),
                         round(video_length * 0.05),
                         round(video_length * 0.075),
                         round(video_length * 0.1),
                         round(video_length * 0.125),
                         round(video_length * 0.15),
                         round(video_length * 0.175),
                         round(video_length * 0.2),
                         round(video_length * 0.25)]
        count = 0
        frames_needed_count = 0
        success, image = cap.read()
        while success and frames_needed_count < THUMB_FRAMES:
            if count in frame_ids:
                frames.append(image)
                frames_needed_count += 1
            success, image = cap.read()
            count += 1
        cap.release()
    return frames


def image_to_thumbs(img):
    """Create thumbs from image"""
    height, width, channels = img.shape
    # thumbs = {"original": img}
    # sizes = [640, 320, 160]
    thumbs = {}
    sizes = [THUMB_SIZE]
    for size in sizes:
        if width >= size:
            r = (size + 0.0) / width
            max_size = (size, int(height * r))
            thumbs[str(size)] = cv2.resize(img, max_size, interpolation=cv2.INTER_AREA)
    return thumbs


def remove_folder_if_exists(folder_path):
    folder = Path(folder_path)
    if folder.exists() and folder.is_dir():
        shutil.rmtree(folder_path, ignore_errors=True)


def remove_file_if_exists(file_path):
    file = Path(file_path)
    if file.exists() and file.is_file():
        os.remove(file_path)


def get_string_strip_suffix(text, suffix):
    logging.info("get_string_without_suffix for %s ", text)
    if not text.endswith(suffix):
        logging.info("return get_string_without_suffix %s ", text)
        return text
    # else
    return text[:len(text) - len(suffix)]


def check_valid_file(video_path, file_ext):
    logging.info("Verifying check_valid_file %s ", video_path)
    if not str(video_path).endswith(tuple(file_ext)):
        logging.error("Failed check_valid_file %s Not an %s ", video_path, file_ext)
        return False
    video_file = Path(video_path)
    try:
        if video_file.exists() and video_file.is_file():
            return True
    except FileNotFoundError:
        logging.error("Failed check_valid_file %s (Not Found) ", video_path)
        return False
    else:
        logging.info("Failed check_valid_file %s ", video_path)
        return False


main()
