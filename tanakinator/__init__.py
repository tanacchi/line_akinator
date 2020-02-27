# Setup for Flask App
import os
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ['TANAKINATOR_SECRET_KEY']


# Setup for Database
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
