import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        # Fix postgres:// URL to postgresql:// for SQLAlchemy 1.4+
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if database_url and database_url.startswith('postgres://'):
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    WTF_CSRF_ENABLED = True
    
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    TMDB_BASE_URL = 'https://api.themoviedb.org/3'
    TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}