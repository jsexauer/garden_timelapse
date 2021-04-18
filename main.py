"""
Python script to periodically capture photos and upload them to Google Photos
"""
import datetime
import logging
import sys

from time import sleep

from google_photos_manager import GooglePhotosManager

now = datetime.datetime.now

def take_picture():
    from picamera import PiCamera

    cam = PiCamera()
    cam.start_preview()
    sleep(5) # Must wait a few seconds to let the picam image adjust
    fn = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    fp = f'/home/pi/projects/garden_timelapse/images/{fn}.jpg'
    cam.capture(fp)
    cam.stop_preview()
    return fp

def main_loop(testing=False):
    # Setup logging
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler("log.txt")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    logging.info("Starting main loop")

    while True:
        # Sleep until next interval
        if testing:
            next_ts = now() + datetime.timedelta(seconds=30)
        else:
            # Take pictures right at noon daily
            if now().hour < 12:
                next_ts = datetime.datetime.now()
            else:
                next_ts = datetime.datetime.now() + datetime.timedelta(days=1)
            next_ts = next_ts.replace(hour=12, minute=0, second=0, microsecond=0)
        wait = (next_ts - datetime.datetime.now()).total_seconds()
        logging.info(f"Waiting {wait:0.1f} seconds until {next_ts}...")
        sleep(wait)

        logging.info("Taking picture")
        fp = take_picture()

        logging.info("Uploading to Google Photos")
        gpm = GooglePhotosManager()
        gpm.upload_photos([fp], "Garden Timelapse")

if __name__ == '__main__':
    main_loop(testing=True)