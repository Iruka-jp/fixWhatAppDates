from restore_exif import *
from gphotospy import authorize
from gphotospy.media import *
from gphotospy.upload import upload
import os, shutil
import json
import mimetypes
import requests

CLIENT_SECRET_FILE = os.path.join( os.getcwd(),'client_secret_687736770496-taigepml0k8efbivikkegl0vscink3rt.apps.googleusercontent.com.json')
UPLOAD_URL = 'https://photoslibrary.googleapis.com/v1/uploads'
CREATE_URL ='https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'

class WhatsAppMediaEditor:

    def __init__(self, year=None,month=None, day=None):
        service = authorize.init(CLIENT_SECRET_FILE)
        self.media_manager = Media(service)
        self.credentials = authorize.get_credentials(CLIENT_SECRET_FILE)
        if year is not None:
            self.backup_date = date(year=year, month=month, day=day)
            self.start_date = date(year=year, month=month, day=day-1)
        else:
            self.backup_date = None

    def __del__(self):
        if len(self.video_list) + len(self.photo_list) >0:
            with open('whatsapp__media.txt', 'w') as file:
                file.write(json.dumps(self.photo_list + self.video_list))
            

    def get_media_list(self):
        photo_list = []
        video_list = []
        
        if os.path.exists('whatsapp__media.txt'):
            with open('whatsapp__media.txt') as f:
                whatsapp_media = json.load(f)
            for media in whatsapp_media:
                if 'image' in media['mimeType']:
                    photo_list.append(media)

                else:
                    video_list.append(media)
        
        else:
            if self.backup_date==None:
                media_iterator = self.media_manager.list()
            else:
                date_interval = date_range(start_date=self.start_date, end_date=self.backup_date)
                media_iterator = self.media_manager.search(date_interval)
            whatsapp_media = [media for media in media_iterator if (is_whatsapp_img(media['filename']) or is_whatsapp_vid(media['filename']))]
            for media in whatsapp_media:
                creation_time = media['mediaMetadata']['creationTime'][:10].replace('-', '')
                file_nametime = media['filename'][4:12]
                if creation_time != file_nametime:
                    if 'image' in media['mimeType']:
                        photo_list.append(media)

                    else:
                        video_list.append(media)

        self.photo_list = photo_list
        self.video_list = video_list


    def process_photos(self, num):
        # Batch download of photos
        os.chdir('photos')
        num = min(len(self.photo_list),num)
        for photo in self.photo_list[:num]:
            with open(photo['filename'], 'wb') as output:
                raw_data = urlopen(photo['baseUrl']).read()
                output.write(raw_data)
        
        photo_list=os.listdir()
        for photo in photo_list:
            self.update_exif(photo)
        response = self.batch_upload(photo_list)
        if response.status_code == 200:
            self.photo_list = self.photo_list[num:]
        os.chdir('..')
        return response
        
    def update_exif(self, media_path):
        exif_dict = piexif.load(media_path)
        if not exif_dict['Exif']:
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = get_exif_datestr(media_path)
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, media_path)
    
    def batch_upload(self, media_list):
        tokens = []
        for media_path in media_list:
            #header['X-Goog-Upload-Content-Type'] = mimetypes.guess_type(media_path)[0]
            #f = open(media_path, 'rb').read()
            #response.append(requests.post(upload_url, data=f, headers=header))
            response = upload(CLIENT_SECRET_FILE, media_path)
            if response is None:
                response = 'Error'
            tokens.append(response)
        return self.create_media(media_list, tokens)
        
    def create_media(self, media_list, tokens):
        mediaItems =[]
        for i, token in enumerate(tokens):
            if token == 'Error':
                continue
            media_item = {
                              "description": "",
                              "simpleMediaItem": {
                                "fileName": media_list[i],
                                "uploadToken": token
                              }
                            }
            mediaItems.append(media_item)
        
        newMediaItems = {
                          "newMediaItems": mediaItems
                        }
        header = {
        'Authorization': "Bearer " + self.credentials.token,
        'Content-type': 'application/json',
        }
        response = requests.post(CREATE_URL, json=newMediaItems, headers=header)
        return response
                
    @staticmethod
    def clear_folders(folder):
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        else:
            os.makedirs(folder)



#if __name__ == 'main':
#    photos_folder = os.path.join(os.getcwd(), 'photos')
#    videos_folder = os.path.join(os.getcwd(), 'videos')

#    WhatsAppMediaEditor.clear_folders(photos_folder)
#    WhatsAppMediaEditor.clear_folders(videos_folder)

#    editor = WhatsAppMediaEditor(year = 2023, month = 9, day = 5)

    #editor.process_photos(10)
