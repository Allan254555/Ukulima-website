import os

class Config:
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join('static','uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
# Ensure upload folder exists
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)
