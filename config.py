"""Flask configuration."""
from os import environ, path

basedir = path.abspath(path.dirname(__file__))

TESTING = True
DEBUG = True
DB_PWD = environ.get('GW_DB_CONNECT')