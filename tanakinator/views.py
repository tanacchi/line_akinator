from flask import render_template, request, abort
from tanakinator import app
from tanakinator.line import handler


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
