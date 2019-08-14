class Config(object):
    # flask default setting
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_POOL_RECYCLE = 1200
    SCHEDULER_API_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "prd"


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "dev"

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "qa"

class StagingConfig(Config):
    DEBUG = False
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "stg"


config = {
    "dev": DevelopmentConfig,
    "qa": TestingConfig,
    "stg": StagingConfig,
    "prd": ProductionConfig,
    "default": DevelopmentConfig,
}
