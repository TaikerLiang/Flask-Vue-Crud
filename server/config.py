import os

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
    SQLALCHEMY_DATABASE_URI = "postgresql://taiker:@{$RDS_HOST}/flask-vue"

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "dev"
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:@{}/{}".format(os.getenv("PGUSER"), os.getenv("PGHOST"), os.getenv("PGDATABASE"))

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "qa"
    SQLALCHEMY_DATABASE_URI = "postgresql://taiker:@{$RDS_HOST}/flask-vue"

class StagingConfig(Config):
    DEBUG = False
    DOMAIN = "http://127.0.0.1:5000"
    BRANCH = "stg"
    SQLALCHEMY_DATABASE_URI = "postgresql://taiker:@{$RDS_HOST}/flask-vue"


config = {
    "dev": DevelopmentConfig,
    "qa": TestingConfig,
    "stg": StagingConfig,
    "prd": ProductionConfig,
    "default": DevelopmentConfig,
}
