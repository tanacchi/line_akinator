import enum

from tanakinator.models import (
    UserStatus, Question, Answer,
    Solution, Feature
)
from tanakinator import db


class GameState(enum.Enum):
    PENDING     = 'pending'
    ASKING      = 'asking'
    GUESSING    = 'guessing'
    RESUMING    = 'resuming'
    BEGGING     = 'begging'
    REGISTERING = 'registering'
    CONFIRMING  = 'confirming'
    TRAINING    = 'training'
    FEATURING   = 'featuring'
    LABELING    = 'labeling'
    UPDATING    = 'updating'


def get_game_status(user_id):
    status = db.session.query(UserStatus).filter_by(user_id=user_id).first()
    return GameState(status.status) if status else GameState.PENDING

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
