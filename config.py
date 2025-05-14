import os

class Config:
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    ALLOWED_EXTENSIONS = {'jpg', 'csv'}