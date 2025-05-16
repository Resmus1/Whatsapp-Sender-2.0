import os

class Config:
    SECRET_KEY = "dfgdfgdfggse4325345ergsertg34t"
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    ALLOWED_EXTENSIONS = {'jpg', 'csv', 'txt'}