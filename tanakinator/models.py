from tanakinator import db


progresses = db.Table('progresses',
    db.Column('progress_id', db.Integer, db.ForeignKey('progress.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
)
candidates = db.Table('candidates',
    db.Column('progress_id', db.Integer, db.ForeignKey('progress.id'), primary_key=True),
    db.Column('solution_id', db.Integer, db.ForeignKey('solution.id'), primary_key=True),
)

class LatestMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False, unique=True)
    message = db.Column(db.String(200), nullable=False)

    def __init__(self, user_id, message):
        self.user_id = user_id
        self.message = message


class UserStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False, unique=True)
    status = db.Column(db.String(80), nullable=False)
    progress = db.relationship('Progress', uselist=False, lazy=True)


class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_status_id = db.Column(db.Integer, db.ForeignKey('user_status.id'))
    answers = db.relationship('Answer', lazy=True)
    latest_question = db.relationship('Question', secondary=progresses, uselist=False, lazy=True)
    candidates = db.relationship('Solution', secondary=candidates, lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    features = db.relationship('Feature', backref='question', lazy=True)
    answers = db.relationship('Answer', backref='question', lazy=True)


class Solution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    features = db.relationship('Feature', backref='solution', lazy=True)


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    solution_id = db.Column(db.Integer, db.ForeignKey('solution.id'))
    value = db.Column(db.Float)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey('progress.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    value = db.Column(db.Float)


def init():
    db.create_all()
