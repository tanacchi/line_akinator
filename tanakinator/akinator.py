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
    related_question_set = set()
    for s in progress.candidates:
        print("s => ", s)
        q_set = {f.question_id for f in s.features}
        print("q_set: ", q_set)
        related_question_set.update(q_set)
    q_score_table = {q_id: 0.0 for q_id in list(related_question_set)}
    print("q_score_table(before): ", q_score_table)
    for s in progress.candidates:
        for q_id in q_score_table:
            feature = Feature.query.filter_by(question_id=q_id, solution_id=s.id).first()
            q_score_table[q_id] += feature.value
    q_score_table = {key: abs(value) for key, value in q_score_table.items()}
    print("q_score_table(after): ", q_score_table)
    next_q_id = min(q_score_table, key=q_score_table.get)
    return Question.query.get(next_q_id)

def save_status(user_status, new_status=None, next_question=None):
    if new_status:
        user_status.status = new_status.value
    if next_question:
        user_status.progress.latest_question = next_question
    db.session.add(user_status)
    db.session.commit()

def update_candidates(progress):
    q_id = progress.latest_question.id
    latest_answer = Answer.query.filter_by(question_id=q_id).order_by(Answer.id.desc()).first()
    s_score_table = {s.id: 0.0 for s in progress.candidates}
    for s_id in s_score_table:
        feature = Feature.query.filter_by(question_id=q_id, solution_id=s_id).first()
        s_score_table[s_id] = latest_answer.value * feature.value
    print("[update_candidates] s_score_table: ", s_score_table)
    new_candidates = [Solution.query.get(s_id) for s_id, score in s_score_table.items() if score >= 0.0]
    return new_candidates

def can_decide(progress):
    return len(progress.candidates) == 1 or len(progress.answers) >= Question.query.count()

def push_answer(progress, answer_msg):
    answer = Answer()
    answer.question = progress.latest_question
    answer.value = 1.0 if answer_msg == "はい" else -1.0
    progress.answers.append(answer)
    db.session.add(answer)
    db.session.commit()

def guess_solution(progress):
    latest_q_id = progress.latest_question.id
    s_score_table = {s.id: 0.0 for s in progress.candidates}
    for s_id in s_score_table:
        for ans in progress.answers:
            feature = Feature.query.filter_by(question_id=ans.question_id, solution_id=s_id).first()
            if not feature: continue
            s_score_table[s_id] += ans.value * feature.value
    print("[guess_solution] s_score_table: ", s_score_table)
    return Solution.query.get(max(s_score_table, key=s_score_table.get))

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
        for c in user_status.progress.candidates:
            print("candidate:: id: {}, name: {}".format(c.id, c.name))
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

