import cv2 as cv
import time
import datetime
from cv2.cv2 import VideoCapture, VideoWriter
import winsound

from seccam.utils import list_ports


class Camera:
    _seconds_to_record_after_raising_alarm: int
    _frame_size: (int, int)
    _fourcc = cv.cv2.VideoWriter_fourcc(*"mp4v")
    _move_detected: bool
    _record_started: bool
    _output_video: VideoWriter

    def __init__(self, seconds_to_record=5):
        """
        Runs loop until a "q" (quit) command is prompted.
        """

        if not isinstance(seconds_to_record, int):
            raise ValueError("The provided tracked_bot_file is not a str")
        self._seconds_to_record_after_raising_alarm = seconds_to_record
        av_ports, wrk_ports = list_ports()
        if len(av_ports) == 0 or wrk_ports == 0:
            raise IOError("No available ports or working ports where found. Exiting with errors")
        # Open first wrk_port in the list. Because it's in there, we know it will be okay to use it for the loop!
        cam = cv.cv2.VideoCapture(wrk_ports[0])
        self._frame_size = (int(cam.get(3)), int(cam.get(4)))
        self._move_detected = False
        self._record_started = False
        while cam.isOpened():
            frame, movement = self.check_for_movement(cam)
            if movement:
                self._move_detected = True
                self.save_video()
            if cv.cv2.waitKey(10) == ord('q'):
                break

        self.close_all_frames([cam])

    def close_all_frames(self, frames: list):
        """
        Given a list of frames, closes them all and quits the camera windows.
        :param frames: list of frames. Each frame should be a VideoCapture object from cv2
        :return:
        """

        for frame in frames:
            frame.release()
        cv.cv2.destroyAllWindows()
        return

    def check_for_movement(self, camera: VideoCapture):
        """
        Compares two consecutive frames captured by the camera. If there's movement detected, it reproduces an alarm sound.
        :param camera: VideoCapture object
        :return: frame, boolean with a true or false statement about the movement detection.
        """

        movement = False
        ret, frame1 = camera.read()
        ret, frame2 = camera.read()
        diff = cv.cv2.absdiff(frame1, frame2)
        # Turn diff into gray scale
        gray = cv.cv2.cvtColor(diff, cv.cv2.COLOR_RGB2GRAY)
        # apply gaussian blur?
        blur = cv.cv2.GaussianBlur(gray, (5, 5), 0)
        _, threshold = cv.cv2.threshold(blur, 20, 255, cv.cv2.THRESH_BINARY)
        dilated = cv.cv2.dilate(threshold, None, iterations=3)
        contours, _ = cv.cv2.findContours(dilated, cv.cv2.RETR_TREE, cv.cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(frame1, contours, -1, (0, 255, 0), 2)
        for c in contours:
            if cv.cv2.contourArea(c) < 5000:
                continue
            x, y, w, h = cv.cv2.boundingRect(c)
            cv.cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Movement detected, raise alarm
            winsound.PlaySound('../sources/alarm.wav', winsound.SND_ASYNC)
            movement = True

        # We return a frame to display
        return frame1, movement

    def save_video(self):
        current_time = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        alarm_stop_time: time
        if not self._record_started:
            self._output_video = cv.cv2.VideoWriter(f"{current_time}.mp4", self._fourcc, 20, self._frame_size)
            # Start recording!
            self._record_started = True
            alarm_stop_time = time.time()
        elif self._record_started:
            if time.time() - alarm_stop_time >= self._seconds_to_record_after_raising_alarm:
                # Stop recording
                self._record_started = False
                self._move_detected = False
                self._output_video.release()
