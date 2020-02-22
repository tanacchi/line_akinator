from tanakinator.common import GameState
from tanakinator.models import (
    UserStatus, Question, Answer,
    Solution, Feature
)
from tanakinator import db


def get_game_status(user_id):
    status = db.session.query(UserStatus).filter_by(user_id=user_id).first()
    return GameState(status.status) if status else GameState.PENDING

def get_user_status(user_id):
    user_status = db.session.query(UserStatus).filter_by(user_id=user_id).first()
    if not user_status:
        user_status = UserStatus()
        user_status.user_id = user_id
        user_status.status = GameState.PENDING.value
        db.session.add(user_status)
        db.session.commit()
    return user_status

def select_next_question(progress):
    all_questions = Question.query.all()
    return all_questions[len(progress.answers)]

def save_status(user_status, new_status=None, next_question=None):
    if new_status:
        user_status.status = new_status.value
    if next_question:
        user_status.progress.latest_question = next_question
    db.session.add(user_status)
    db.session.commit()

def can_guess(progress):
    return len(progress.answers) >= len(Question.query.all())

def push_answer(progress, answer_msg):
    answer = Answer()
    answer.question = progress.latest_question
    answer.value = 1.0 if answer_msg == "はい" else -1.0
    progress.answers.append(answer)
    db.session.add(answer)
    db.session.commit()

def guess_solution(progress):
    score_table = {s.id: 0.0 for s in Solution.query.all()}
    for ans in progress.answers:
        q_features = Feature.query.filter_by(question_id=ans.question_id)
        for f in q_features:
            score_table[f.solution.id] += ans.value * f.value
    return Solution.query.get(max(score_table, key=score_table.get))

def get_feature_table():
    result = {
        "S1": {"Q1": 1.0, "Q2": 0.0, "Q3": 1.0},
        "S2": {"Q1": 1.0, "Q2": 1.0, "Q3": 0.0},
        "S3": {"Q1": 0.0, "Q2": 1.0, "Q3": 0.0},
        "S4": {"Q1": 1.0, "Q2": 0.0, "Q3": 0.0},
    }
    return result


def test():
    answers = []
    all_questions = Question.query.all()
    print(all_questions)

    while len(answers) < len(all_questions):
        q = all_questions[len(answers)]
        ans_msg = input(q.message + "[y/n]")
        if not ans_msg in ['y', 'n']:
            raise RuntimeError("Invalid answer.")
        answer = Answer()
        answer.question = q
        answer.value = 1.0 if ans_msg == 'y' else -1.0
        answers.append(answer)
        db.session.add(answer)
        db.session.commit()
        print(answers)

        score_table = {s.id: 0.0 for s in Solution.query.all()}
        for ans in answers:
            q_features = db.session.query(Feature).filter_by(question_id=ans.question.id)
            for f in q_features:
                score_table[f.solution.id] += ans.value * f.value
        print(score_table)

    most_likely_solution = Solution.query.get(max(score_table, key=score_table.get))
    print(most_likely_solution.name)
