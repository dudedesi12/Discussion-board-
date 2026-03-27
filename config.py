import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    _db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///immi_pink.db'
    if _db_uri.startswith('postgres://'):
        _db_uri = _db_uri.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
