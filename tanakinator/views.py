from collections import defaultdict

from flask import render_template, request, abort
from tanakinator import app, handler

from tanakinator.akinator import get_feature_table

CIRCLE_CHAR = '&#9675;'
CROSS_CHAR  = '&#10005;'

@app.route('/')
def root():
    feature_table = get_feature_table()
    table = defaultdict(dict)
    solutions, questions = {}, {}
    for solution_id, features in feature_table.items():
        solutions[solution_id] = solution_id     # FIXME: Use solution name.
        for question_id, value in features.items():
            questions[question_id] = question_id # FIXME: Use question name.
            if value == 1.0:
                table[solution_id][question_id] = CIRCLE_CHAR
            else:
                table[solution_id][question_id] = CROSS_CHAR
    return render_template('index.html', solutions=solutions, questions=questions, table=table)


from linebot.exceptions import InvalidSignatureError

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
