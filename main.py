from seccam.camera import Camera


def main():
    # Start the camera loop. TODO: Add optional parameters to redirect the output and duration time of the recordings
    Camera(seconds_to_record=6)


if __name__ == "__main__":
    main()
