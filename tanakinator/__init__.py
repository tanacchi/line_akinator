# Setup for Flask App
from flask import Flask

app = Flask(__name__)


# Setup for LineBot
from linebot import (
    LineBotApi, WebhookHandler
)
import os

CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET       = os.environ['CHANNEL_SECRET']

line    = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# Including other scripts
import tanakinator.views
