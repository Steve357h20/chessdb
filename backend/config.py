import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    STOCKFISH_PATH = os.environ.get('STOCKFISH_PATH', os.path.join(os.path.dirname(__file__), 'stockfish', 'stockfish', 'stockfish-windows-x86-64-avx2.exe'))
    ANALYSIS_DEPTH = int(os.environ.get('ANALYSIS_DEPTH', 20))
    ANALYSIS_TIMEOUT = int(os.environ.get('ANALYSIS_TIMEOUT', 300))
    ANALYSIS_THREADS = int(os.environ.get('ANALYSIS_THREADS', 1))
    ANALYSIS_HASH = int(os.environ.get('ANALYSIS_HASH', 256))

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'chessdb.db')
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'chessdb.db')
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'test_chess.db')
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
