import os
from datetime import timedelta

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    UPLOAD_FOLDER = os.path.abspath('./uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB file size limit
    
    # JWT settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # MongoDB settings
    # MONGO_URI = os.environ.get('MONGO_URI') 
    MONGO_URI = 'mongodb+srv://shettyPrathamesh:120208@cluster0.4icayq9.mongodb.net/file_share_db?retryWrites=true&w=majority&appName=Cluster0'
    # File expiration time in days
    FILE_EXPIRATION_DAYS = 3