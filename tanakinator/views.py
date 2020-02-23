from collections import defaultdict

from flask import (
    render_template, request,
    abort, redirect, url_for
)
from tanakinator import app, handler, db
from tanakinator.models import Solution, Question, Feature
from tanakinator.akinator import get_feature_table

CIRCLE_CHAR = '&#9675;'
CROSS_CHAR  = '&#10005;'

str_value_table = {
    "はい":    1.0,
    None:      0.0,
    "いいえ": -1.0
}

@app.route('/')
def root():
    feature_table = get_feature_table()
    table = defaultdict(dict)
    solutions = {s.id: s.name    for s in Solution.query.all()}
    questions = {q.id: q.message for q in Question.query.all()}
    for s_id, features in feature_table.items():
        for q_id, value in features.items():
            table[s_id][q_id] = CIRCLE_CHAR if value == 1.0 else CROSS_CHAR
    return render_template('index.html', solutions=solutions, questions=questions, table=table)

@app.route('/solutions/create', methods=['GET', 'POST'])
def solution_create():
    if request.method == 'GET':
        questions = Question.query.all()
        return render_template('solutions/create.html', questions=questions)
    else:
        new_solution = Solution()
        new_solution.name = request.form.get("name")
        for attr, value in request.form.items():
            if attr == 'name':
                new_solution.name = value
            else:
                q_id = int(attr[2:])
                feature = Feature()
                feature.question_id = q_id
                feature.value = str_value_table[request.form.get(f"q_{q_id}")]
                new_solution.features.append(feature)
        db.session.add(new_solution)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/solutions/<int:solution_id>/edit', methods=['GET', 'POST'])
def solution_edit(solution_id):
    solution = Solution.query.get(solution_id)
    if request.method == 'GET':
        feature_table = {f: Question.query.get(f.question_id) for f in solution.features}
        kwargs = {'solution': solution, 'feature_table': feature_table}
        return render_template('solutions/edit.html', **kwargs)
    else:
        for f in solution.features:
            f.value = str_value_table[request.form.get(f"q_{f.question_id}")]
        db.session.add(solution)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/questions/create', methods=['GET', 'POST'])
def question_create():
    if request.method == 'GET':
        return render_template('questions/create.html')
    else:
        new_question = Question()
        new_question.message = request.form.get("message")
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('root'))


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
