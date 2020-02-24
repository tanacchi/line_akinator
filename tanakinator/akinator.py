from collections import defaultdict

from tanakinator.common import GameState, TextMessageForm, QuickMessageForm
from tanakinator.models import (
    UserStatus, Question, Answer,
    Solution, Feature, Progress
)
from tanakinator import db


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

def update_candidates(progress):
    score_table = {s.id: 0.0 for s in progress.candidates}
    for ans in progress.answers:
        q_features = Feature.query.filter_by(question_id=ans.question_id)
        for f in q_features:
            score_table[f.solution_id] += ans.value * f.value
    return [Solution.query.get(s_id) for s_id, score in score_table.items() if score >= 0.0]

def can_decide(progress):
    return len(progress.answers) >= len(Question.query.all())

def push_answer(progress, answer_msg):
    answer = Answer()
    answer.question = progress.latest_question
    answer.value = 1.0 if answer_msg == "はい" else -1.0
    progress.answers.append(answer)
    db.session.add(answer)
    db.session.commit()

def guess_solution(progress):
    score_table = {s.id: 0.0 for s in progress.candidates}
    for ans in progress.answers:
        q_features = Feature.query.filter_by(question_id=ans.question_id)
        for f in q_features:
            score_table[f.solution.id] += ans.value * f.value
    return Solution.query.get(max(score_table, key=score_table.get))

def handle_pending(user_status, message):
    reply_content = []
    if message == "はじめる":
        user_status.progress = Progress()
        user_status.progress.candidates = Solution.query.all()
        question = select_next_question(user_status.progress)
        save_status(user_status, GameState.ASKING, question)
        reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
    else:
        reply_content.append(QuickMessageForm(text="「はじめる」をタップ！", items=["はじめる"]))
    return reply_content

def handle_asking(user_status, message):
    reply_content = []
    if message in ["はい", "いいえ"]:
        push_answer(user_status.progress, message)
        user_status.progress.candidates = update_candidates(user_status.progress)
        if not can_decide(user_status.progress):
            question = select_next_question(user_status.progress)
            save_status(user_status, next_question=question)
            reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
        else:
            most_likely_solution = guess_solution(user_status.progress)
            reply_text = "思い浮かべているのは\n\n" + most_likely_solution.name + "\n\nですか?"
            save_status(user_status, GameState.GUESSING)
            reply_content.append(QuickMessageForm(text=reply_text, items=["はい", "いいえ"]))
    else:
        reply_content.append(TextMessageForm(text="Pardon?"))
    return reply_content

def handle_guessing(user_status, message):
    reply_content = []
    if message in ["はい", "いいえ"]:
        reply_text = "やったー" if message == "はい" else "ええ〜"
        db.session.query(Answer).filter_by(progress_id=user_status.progress.id).delete()
        db.session.delete(user_status.progress)
        save_status(user_status, GameState.PENDING)
    else:
        reply_text = "Pardon?"
    reply_content.append(TextMessageForm(text=reply_text))
    return reply_content

