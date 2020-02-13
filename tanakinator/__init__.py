# Setup for Flask App
from flask import Flask

app = Flask(__name__)


# Setup for LineBot
from linebot import (
    LineBotApi, WebhookHandler
)
import os

LOCAL_MODE = os.environ.get('TANAKINATOR_LOCAL_MODE')

if not LOCAL_MODE:
    CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
    CHANNEL_SECRET       = os.environ.get('CHANNEL_SECRET')

    line    = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
else:
    line    = None
    handler = None


# Including other scripts
if not LOCAL_MODE:
    import tanakinator.line
import tanakinator.views
