# Hooked-Forumist Flask App

Hooked-Forumist is a Flask application that provides a webhook endpoint for uploading files to multiple file hosting services concurrently. It allows users to upload a file and automatically distributes it to different file hosting platforms, such as Pixeldrain and Baidupan. The application provides JSON responses for various endpoints.

## Prerequisites

Before running the Hooked-Forumist Flask app, ensure you have the following prerequisites installed:

- Python 3.x
- Flask
- requests
- baidupcs-py

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/chiabautsai/hooked-forumist.git
   ```

2. Change into the project directory:

   ```bash
   cd hooked-forumist
   ```

3. Install the required dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

To configure the Hooked-Forumist Flask app, follow these steps:

1. Set the environment variables `BDUSS` and `STOKEN` with your Baidu PCS API credentials. These variables are required for the BaidupanHandler to function properly.

## Developer

To run the Hooked-Forumist Flask app in development, execute the following command in the project directory:

```bash
flask run
```

The Flask development server will start running on `http://localhost:5000/`.

## Endpoints

### Greet

- **URL:** `/`
- **Method:** GET
- **Description:** Greet the user with a JSON response.
- **Response:**
  ```json
  {
    "message": "Hello!"
  }
  ```

### Handle Webhook

- **URL:** `/webhook`
- **Method:** POST
- **Description:** Handle the webhook request to upload a file to multiple file hosting services.
- **Request Body:**
  ```json
  {
    "file_path": "/path/to/file"
  }
  ```
- **Response (Success):**
  ```json
  {
    "success": true,
    "value": [
      {
        "download_url": "https://example.com/url",
        "password": null
      },
      {
        "download_url": "https://example.com/url2",
        "password": "examplepassword"
      }
    ]
  }
  ```
- **Response (Failure - Invalid Request):**
  ```json
  {
    "success": false,
    "message": "Invalid request",
    "value": null
  }
  ```
- **Response (Failure - Server Error):**
  ```json
  {
    "success": false,
    "message": "Server Error",
    "value": null
  }
  ```

## File Hosting Handlers

The `app/file_uploader.py` file contains two file hosting handlers:

1. **PixeldrainHandler:** Handles file uploading to Pixeldrain.
2. **BaidupanHandler:** Handles file uploading to Baidupan.

You can extend the functionality of the application by adding more file hosting handlers in the `app/file_uploader.py` file and using them in the `app/routes.py` file.

## License

This project is licensed under the [GNU v3](LICENSE).

## Contributing

Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please open an issue or submit a pull request.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/): A lightweight WSGI web application framework.
- [BaiduPCS-Py](https://github.com/PeterDing/BaiduPCS-Py.git): A Python client library for Baidu PCS API.
- [Pixeldrain API](http://pixeldrain.com/api): API documentation for Pixeldrain file hosting service.