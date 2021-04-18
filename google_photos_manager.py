import json
import logging
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

mkpath = os.path.join

class GooglePhotosManager:
    """Modified from: https://github.com/eshmu/gphotos-upload/blob/master/upload.py"""
    def __init__(self, basepath):
        self.session = self.get_authorized_session()
        self.basepath = basepath

    def upload_photos(self, photo_file_list, album_name):

        album_id = self.create_or_retrieve_album(album_name) if album_name else None

        # interrupt upload if an upload was requested but could not be created
        if album_name and not album_id:
            return

        self.session.headers["Content-type"] = "application/octet-stream"
        self.session.headers["X-Goog-Upload-Protocol"] = "raw"

        for photo_file_name in photo_file_list:

            try:
                photo_file = open(photo_file_name, mode='rb')
                photo_bytes = photo_file.read()
            except OSError as err:
                logging.error("Could not read file \'{0}\' -- {1}".format(photo_file_name, err))
                continue

            self.session.headers["X-Goog-Upload-File-Name"] = os.path.basename(photo_file_name)

            logging.info("Uploading photo -- \'{}\'".format(photo_file_name))

            upload_token = self.session.post('https://photoslibrary.googleapis.com/v1/uploads', photo_bytes)

            if (upload_token.status_code == 200) and (upload_token.content):

                create_body = json.dumps({"albumId": album_id, "newMediaItems": [
                    {"description": "", "simpleMediaItem": {"uploadToken": upload_token.content.decode()}}]}, indent=4)

                resp = self.session.post('https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate',
                                    create_body).json()

                logging.debug("Server response: {}".format(resp))

                if "newMediaItemResults" in resp:
                    status = resp["newMediaItemResults"][0]["status"]
                    if status.get("code") and (status.get("code") > 0):
                        logging.error(
                            "Could not add \'{0}\' to library -- {1}".format(os.path.basename(photo_file_name),
                                                                             status["message"]))
                    else:
                        logging.info(
                            "Added \'{}\' to library and album \'{}\' ".format(os.path.basename(photo_file_name),
                                                                               album_name))
                else:
                    logging.error("Could not add \'{0}\' to library. Server Response -- {1}".format(
                        os.path.basename(photo_file_name), resp))

            else:
                logging.error(
                    "Could not upload \'{0}\'. Server Response - {1}".format(os.path.basename(photo_file_name),
                                                                             upload_token))

        try:
            del (self.session.headers["Content-type"])
            del (self.session.headers["X-Goog-Upload-Protocol"])
            del (self.session.headers["X-Goog-Upload-File-Name"])
        except KeyError:
            pass

    def create_or_retrieve_album(self, album_title):

        # Find albums created by this app to see if one matches album_title
        for a in self.get_albums(True):
            if a["title"].lower() == album_title.lower():
                album_id = a["id"]
                logging.info("Uploading into EXISTING photo album -- \'{0}\'".format(album_title))
                return album_id

        # No matches, create new album

        create_album_body = json.dumps({"album": {"title": album_title}})
        # print(create_album_body)
        resp = self.session.post('https://photoslibrary.googleapis.com/v1/albums', create_album_body).json()

        logging.debug("Server response: {}".format(resp))

        if "id" in resp:
            logging.info("Uploading into NEW photo album -- \'{0}\'".format(album_title))
            return resp['id']
        else:
            logging.error(
                "Could not find or create photo album '\{0}\'. Server Response: {1}".format(album_title, resp))
            return None

    def get_albums(self, appCreatedOnly=False):

        params = {
            'excludeNonAppCreatedData': appCreatedOnly
        }

        while True:

            albums = self.session.get('https://photoslibrary.googleapis.com/v1/albums', params=params).json()

            logging.debug("Server response: {}".format(albums))

            if 'albums' in albums:

                for a in albums["albums"]:
                    yield a

                if 'nextPageToken' in albums:
                    params["pageToken"] = albums["nextPageToken"]
                else:
                    return

            else:
                return

    def auth(self, scopes):
        flow = InstalledAppFlow.from_client_secrets_file(
            mkpath(self.basepath, 'client_id_secret.json'),
            scopes=scopes)
        credentials = flow.run_local_server(host='localhost',
                                            port=8080,
                                            authorization_prompt_message="",
                                            success_message='The auth flow is complete; you may close this window.',
                                            open_browser=True)

        return credentials

    def get_authorized_session(self):


        scopes = ['https://www.googleapis.com/auth/photoslibrary',
                  'https://www.googleapis.com/auth/photoslibrary.sharing']

        cred = None

        auth_token_file = mkpath(self.basepath, 'auth_session_secret.json')

        if os.path.isfile(auth_token_file):
            try:
                cred = Credentials.from_authorized_user_file(auth_token_file, scopes)
            except OSError as err:
                logging.debug("Error opening auth token file - {0}".format(err))
            except ValueError:
                logging.debug("Error loading auth tokens - Incorrect format")

        if not cred:
            cred = self.auth(scopes)

        session = AuthorizedSession(cred)

        try:
            cred_dict = {
                'token': cred.token,
                'refresh_token': cred.refresh_token,
                'id_token': cred.id_token,
                'scopes': cred.scopes,
                'token_uri': cred.token_uri,
                'client_id': cred.client_id,
                'client_secret': cred.client_secret
            }

            with open(auth_token_file, 'w') as f:
                f.write(json.dumps(cred_dict))

        except OSError as err:
            logging.debug("Could not save auth tokens - {0}".format(err))


        return session

if __name__ == '__main__':
    p = GooglePhotosManager(".")
    print(list(p.get_albums()))