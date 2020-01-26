from flask import render_template, request, abort
from tanakinator import app, line, handler

from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/line', methods=['POST'])
def line_webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature.")
        print("Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line.reply_message(
        event.reply_token,
        TextSendMessage(text="Hello."))
