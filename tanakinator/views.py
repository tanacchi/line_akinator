from collections import defaultdict

from flask import (
    render_template, request,
    abort, redirect, url_for
)
from tanakinator import app, handler, db
from tanakinator.models import Solution, Question, Feature


CIRCLE_CHAR = '&#9675;'
CROSS_CHAR  = '&#10005;'

str_value_table = {
    "はい":    1.0,
    None:      0.0,
    "いいえ": -1.0
}

@app.route('/')
def root():
    solutions = {s.id: s.name    for s in Solution.query.all()}
    questions = {q.id: q.message for q in Question.query.all()}
    features = Feature.query.all()
    table = {s_id: {q_id: '-' for q_id in questions} for s_id in solutions}
    for feature in features:
        s_id, q_id = feature.solution_id, feature.question_id
        table[s_id][q_id] = CIRCLE_CHAR if feature.value == 1.0 else CROSS_CHAR
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
                if value == "": return redirect(url_for('solution_create'))
                new_solution.name = value
            else:
                q_id = int(attr[2:])
                feature = Feature()
                feature.question_id = q_id
                feature.value = str_value_table[value]
                new_solution.features.append(feature)
        db.session.add(new_solution)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/solutions/<int:solution_id>/edit', methods=['GET', 'POST'])
def solution_edit(solution_id):
    solution = Solution.query.get(solution_id)
    if request.method == 'GET':
        known_feature_table = {f: Question.query.get(f.question_id) for f in solution.features}
        unknown_questions = set(Question.query.all()) - {q for q in known_feature_table.values()}
        kwargs = {
            'solution': solution,
            'known_feature_table': known_feature_table,
            'unknown_questions': unknown_questions
        }
        return render_template('solutions/edit.html', **kwargs)
    else:
        for label, value in request.form.items():
            q_id = int(label[2:])
            feature = Feature.query.filter_by(question_id=q_id, solution_id=solution.id).first()
            if not feature:
                feature = Feature()
                feature.question_id = q_id
                feature.solution_id = solution.id
            feature.value = str_value_table[value]
            solution.features.append(feature)
        db.session.add(solution)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/questions/create', methods=['GET', 'POST'])
def question_create():
    if request.method == 'GET':
        solutions = Solution.query.all()
        return render_template('questions/create.html', solutions=solutions)
    else:
        new_question = Question()
        for attr, value in request.form.items():
            if attr == 'message':
                message = request.form.get('message')
                if message == "": return redirect(url_for('question_create'))
                new_question.message = message
            else:
                s_id = int(attr[2:])
                feature = Feature()
                feature.solution_id = s_id
                feature.value = str_value_table[value]
                new_question.features.append(feature)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
def question_edit(question_id):
    question = Question.query.get(question_id)
    if request.method == 'GET':
        return render_template('questions/edit.html', question=question)
    else:
        question.message = request.form.get("message")
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('root'))

@app.route('/features/edit', methods=['GET', 'POST'])
def feature_edit():
    if request.method == 'GET':
        s_id, q_id = request.args.get('s_id'), request.args.get('q_id')
        solution = Solution.query.get(s_id)
        question = Question.query.get(q_id)
        feature = Feature.query.filter_by(solution_id=s_id, question_id=q_id).first() or Feature()
        return render_template('features/edit.html', solution=solution, question=question, feature=feature)
    else:
        s_id, q_id = request.form.get('solution_id'), request.form.get('question_id')
        feature = Feature.query.filter_by(solution_id=s_id, question_id=q_id).first()
        if not feature:
            feature = Feature()
            feature.solution_id = s_id
            feature.question_id = q_id
        feature.value = str_value_table[request.form.get('value')]
        db.session.add(feature)
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
