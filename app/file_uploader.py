import os, random, string, threading, hashlib
import requests
from abc import ABC, abstractmethod

from baidupcs_py.baidupcs import BaiduPCSApi

class FileHostHandler(ABC):
    @abstractmethod
    def upload_file(self, file_path):
        pass

    @abstractmethod
    def get_download_url(self):
        pass

    @abstractmethod
    def get_password(self):
        pass

    def hash_filename(self, filename):
        # Extract the file extension
        _, ext = os.path.splitext(filename)

        # Compute the hash of the filename without the extension
        hasher = hashlib.sha256()
        hasher.update(os.path.splitext(filename)[0].encode('utf-8'))
        hashed_name = hasher.hexdigest()

        # Concatenate the hashed name with the original file extension
        return hashed_name + ext

class PixeldrainHandler(FileHostHandler):
    BASE_URL = 'https://pixeldrain.com/api'
    UPLOAD_URL = BASE_URL + '/file/{name}'

    def __init__(self):
        self.session = requests.Session()
        self.file_id = None

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                # Send a PUT request to API endpoint
                # Note: Do not use 'files' attribute as PUT endpoint does
                # not accept multipart encoding files
                hashed_name = self.hash_filename(os.path.basename(file.name))
                response = self.session.put(
                    self.UPLOAD_URL.format(name=hashed_name),
                    data=file)

                if response.status_code == 201:
                    response_json = response.json()
                    self.file_id = response_json['id']
                    return True
                else:
                    raise Exception(f'Error Response: {response.content}')

        except IOError as e:
            print(f"Failed to read the file: {e}")
            raise(e)

    def get_download_url(self):
        if self.file_id:
            return f"https://pixeldrain.com/u/{self.file_id}"
        else:
            return None

    def get_password(self):
        return None

class BaidupanHandler(FileHostHandler):
    BDUSS = os.environ.get("BDUSS")
    STOKEN = os.environ.get("STOKEN")
    # Specify a base path on BD pan to upload to
    REMOTE_PATH_BASE = '/junk/'

    def __init__(self):
        self.link = None
        self.password = None
        self.bd = BaiduPCSApi(bduss=self.BDUSS, stoken=self.STOKEN)

    def _generate_share_pwd(self, length=4):
        pool = string.ascii_lowercase + string.digits
        pwd = ''
        for i in range(length):
            pwd += random.choice(pool)
        return pwd

    def upload_file(self, file_path):
        size = os.path.getsize(file_path)
        # Make sure BDUSS and STOKEN are set
        if not self.BDUSS or not self.STOKEN:
            raise Exception('BDUSS or STOKEN not set.')

        try:
            with open(file_path, 'rb') as file:
                hashed_name = self.hash_filename(os.path.basename(file.name))
                remote_path = os.path.join(
                    self.REMOTE_PATH_BASE, hashed_name
                )
                # Upload the file to remote path
                self.bd.upload_file(file, remote_path)

                # Get download link and password
                share_file = self.bd.share(remote_path,
                                           password=self._generate_share_pwd())
                
                self.link, self.password = share_file.url, share_file.password

                # Check if got link and password
                if not self.link or not self.password:
                    raise Exception('Failed to get share link and password')
        except IOError as e:
            print(f"Failed to read the file: {e}")
            raise(e)

    def get_download_url(self):
        return self.link if self.link else None

    def get_password(self):
        return self.password if self.password else None
    
class FileUploader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.uploaded = []

    def upload_to(self, Handler):
        # Implement the logic to upload the file to a single file host
        handler = Handler()
        handler.upload_file(self.file_path)

        self.uploaded.append((handler.get_download_url(), handler.get_password()))

    def upload_to_multiple(self, Handlers):
        # Create a thread for each file host and start the uploads concurrently
        threads = []
        for Handler in Handlers:
            thread = threading.Thread(target=self.upload_to, args=(Handler,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def get_download_urls(self):
        return self.uploaded if self.uploaded else None

def upload(file_path):
    uploader = FileUploader(file_path)
    try:
        uploader.upload_to_multiple([
            BaidupanHandler,
            PixeldrainHandler,
        ])
        uploaded = {
            'file_name': os.path.basename(file_path),
            'download_urls': uploader.get_download_urls(),
        }
        send_upload_complete_request(uploaded)
    except Exception as e:
        print(e)
        # Handle the error if needed

def send_upload_complete_request(uploaded):
    # Placeholder function
    print(uploaded)
    # url = 'https://example.com/upload-complete'
    # try:
    #     response = requests.post(url, json=download_urls)
    #     if response.status_code != 200:
    #         print(f"Failed to send upload complete request. Status code: {response.status_code}")
    # except requests.exceptions.RequestException as e:
    #     print(f"Failed to send upload complete request: {e}")