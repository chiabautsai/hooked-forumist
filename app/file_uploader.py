import os, random, string, threading, hashlib, re, json
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm

from baidupcs_py.baidupcs import BaiduPCSApi

load_dotenv()

class FileHostHandler(ABC):
    @abstractmethod
    def upload_file(self, file_path):
        pass

    @abstractmethod
    def get_download_url(self):
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
                # Get the file size for tqdm progress bar
                file_size = os.path.getsize(file_path)

                # Create the MultipartEncoder with the file data
                hashed_name = self.hash_filename(os.path.basename(file.name))
                multipart_data = MultipartEncoder(fields={'file': (hashed_name, file, 'application/octet-stream')})

                # Custom callback function to track progress
                def progress_callback(monitor):
                    progress_bar.n = monitor.bytes_read
                    progress_bar.refresh()

                # Use MultipartEncoderMonitor to wrap the MultipartEncoder and track progress
                monitor = MultipartEncoderMonitor(multipart_data, progress_callback)

                # Set up tqdm progress bar
                progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc='Uploading', dynamic_ncols=True)

                # Send a PUT request to API endpoint with tqdm to display progress
                response = self.session.put(
                    self.UPLOAD_URL.format(name=hashed_name),
                    data=monitor,  # Use the monitor instead of the file
                    headers={
                        'Content-Type': multipart_data.content_type,
                        'Content-Length': str(file_size),
                        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
                    }
                )

                # Close the tqdm progress bar
                progress_bar.close()

                if response.status_code == 201:
                    response_json = response.json()
                    self.file_id = response_json['id']
                    return True
                else:
                    raise Exception(f'Error Response: {response.content}')

        except IOError as e:
            print(f"Failed to read the file: {e}")
            raise e

    def get_download_url(self):
        if self.file_id:
            return f"https://pixeldrain.com/u/{self.file_id}"
        else:
            return None

class BaidupanHandler(FileHostHandler):
    BDUSS = os.environ.get("BDUSS")
    STOKEN = os.environ.get("STOKEN")
    # Specify a base path on BD pan to upload to
    REMOTE_PATH_BASE = '/junk/'

    def __init__(self):
        self.link = None
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
                file_size = os.path.getsize(file_path)

                # Set up tqdm progress bar
                with tqdm(total=file_size, unit='B', unit_scale=True, desc='Uploading', dynamic_ncols=True) as progress_bar:
                    # Define the callback function to update the progress bar
                    def progress_callback(monitor):
                        progress_bar.update(monitor.bytes_read - progress_bar.n)

                    # Use requests_toolbelt's MultipartEncoderMonitor to track progress
                    hashed_name = self.hash_filename(os.path.basename(file.name))
                    remote_path = os.path.join(self.REMOTE_PATH_BASE, hashed_name)
                    self.bd.upload_file(
                        file,
                        remote_path,
                        callback=progress_callback  # Pass the progress_callback to the upload_file method
                    )

                # Get download link and password
                share_file = self.bd.share(remote_path,
                                           password=self._generate_share_pwd())
                
                link, password = share_file.url, share_file.password

                # Check if got link and password
                if not link or not password:
                    raise Exception('Failed to get share link and password')
                
                self.link = f'{share_file.url}?pwd={share_file.password}'
        except IOError as e:
            print(f"Failed to read the file: {e}")
            raise(e)

    def get_download_url(self):
        return self.link if self.link else None
    
class FileUploader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.uploaded = []

    def upload_to(self, Handler):
        # Implement the logic to upload the file to a single file host
        handler = Handler()
        handler.upload_file(self.file_path)

        self.uploaded.append(handler.get_download_url())

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
        file_name = os.path.basename(file_path)
        uploader.upload_to_multiple([
            BaidupanHandler,
            PixeldrainHandler,
        ])
        uploaded = {
            'file_name': file_name,
            'file_size': os.path.getsize(file_path),
            'pre_name': if_scn_release(file_name),
            'download_urls': list(filter(None, uploader.get_download_urls())),
        }

        send_upload_complete_request(uploaded)
    except Exception as e:
        print(e)
        # Handle the error if needed

def if_scn_release(file_name):
    pattern = r"\[.*?\]_(.*?-\d{4}-[A-Za-z0-9]+\.(?:tar|zip|rar|7z))"
    matched_pre_name = re.search(pattern, file_name)

    return matched_pre_name.group(1) if matched_pre_name else None

def send_upload_complete_request(uploaded):
    print(json.dumps(uploaded, indent=4))
    url = os.environ.get("API_ENDPOINT")
    try:
        response = requests.post(url, json=uploaded)
        if response.status_code != 200:
            print(f"Failed to send upload complete request. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send upload complete request: {e}")