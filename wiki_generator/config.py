from pydantic import BaseModel


class BaseConfig(object):
    SECRET_KEY = 'secret key'
    INDEX_PER_PAGE = 9
    ADMIN_PER_PAGE = 15
    DEBUG = True
    MONGO_DB_URL = "mongodb://localhost:27017" #to run from docker container use "mongodb://mongo:27017"
    MONGO_DB_NAME = "Croco_Wiki"


settings =  BaseConfig()