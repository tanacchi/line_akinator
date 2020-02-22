# Setup for Flask App
from flask import Flask

app = Flask(__name__)


# Setup for Database
import os
from flask_sqlalchemy import SQLAlchemy

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///local.db'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


# Setup for LineBot
from linebot import (
    LineBotApi, WebhookHandler
)

CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET       = os.environ['CHANNEL_SECRET']

line    = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# Including other scripts
import tanakinator.line
import tanakinator.views
