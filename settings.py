DEBUG = False

DATABASE_PATH = "scores.sqlite"

BITLY_LOGIN = ""
BITLY_API_KEY = ""
TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_ACCESS_TOKEN_KEY = ""
TWITTER_ACCESS_TOKEN_SECRET = ""


try:
    from settings_my import *
except ImportError:
    pass