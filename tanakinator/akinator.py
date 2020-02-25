from collections import OrderedDict
from statistics import mean

from tanakinator.common import GameState, TextMessageForm, QuickMessageForm
from tanakinator.models import (
    UserStatus, Question, Answer,
    Solution, Feature, Progress,
    PreparedSolution
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
        q_set = {f.question_id for f in s.features}
        related_question_set.update(q_set)
    q_score_table = {q_id: 0.0 for q_id in list(related_question_set)}
    for s in progress.candidates:
        for q_id in q_score_table:
            feature = Feature.query.filter_by(question_id=q_id, solution_id=s.id).first()
            q_score_table[q_id] += feature.value if feature else 0.0
    q_score_table = {key: abs(value) for key, value in q_score_table.items()}
    print("[select_next_question] q_score_table: ", q_score_table)
    next_q_id = min(q_score_table, key=q_score_table.get)
    return Question.query.get(next_q_id)

def save_status(user_status, new_status=None, next_question=None):
    if new_status:
        user_status.status = new_status.value
    if next_question:
        user_status.progress.latest_question = next_question
    db.session.add(user_status)
    db.session.commit()

def reset_status(user_status):
    db.session.query(Answer).filter_by(progress_id=user_status.progress.id).delete()
    db.session.delete(user_status.progress)
    save_status(user_status, GameState.PENDING)

def gen_solution_score_table(progress):
    s_score_table = {s.id: 0.0 for s in progress.candidates}
    for s_id in s_score_table:
        for ans in progress.answers:
            feature = Feature.query.filter_by(question_id=ans.question_id, solution_id=s_id).first()
            s_score_table[s_id] += ans.value * (feature.value if feature else 0.0)
    s_score_table = OrderedDict(sorted(s_score_table.items(), key=lambda x: x[1]))
    print("s_score_table: ", s_score_table)
    return s_score_table

def update_candidates(s_score_table):
    score_mean = mean(s_score_table.values())
    return [Solution.query.get(s_id) for s_id, score in s_score_table.items() if score >= score_mean]

def can_decide(s_score_table, old_s_score_table):
    scores = list(s_score_table.values())
    return len(scores) == 1 or scores[0] != scores[1] or s_score_table.keys() == old_s_score_table.keys()

def push_answer(progress, answer_msg):
    answer = Answer()
    answer.question = progress.latest_question
    answer.value = 1.0 if answer_msg == "はい" else -1.0
    progress.answers.append(answer)
    db.session.add(answer)
    db.session.commit()

def guess_solution(s_score_table):
    return Solution.query.get(max(s_score_table, key=s_score_table.get))

def update_features(progress, true_solution=None):
    solution = true_solution or guess_solution(gen_solution_score_table(progress))
    qid_feature_table = {f.question_id: f for f in solution.features}
    for ans in progress.answers:
        if ans.question_id in qid_feature_table:
            feature = qid_feature_table[ans.question_id]
        else:
            feature = Feature()
            feature.question_id = ans.question_id
            feature.solution_id = solution.id
        feature.value = ans.value
        db.session.add(feature)
        db.session.commit()

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
        old_s_score_table = gen_solution_score_table(user_status.progress)
        user_status.progress.candidates = update_candidates(old_s_score_table)
        for c in user_status.progress.candidates:
            print("candidate:: id: {}, name: {}".format(c.id, c.name))
        s_score_table = gen_solution_score_table(user_status.progress)
        if not can_decide(s_score_table, old_s_score_table):
            question = select_next_question(user_status.progress)
            save_status(user_status, next_question=question)
            reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
        else:
            most_likely_solution = guess_solution(s_score_table)
            reply_text = "思い浮かべているのは\n\n" + most_likely_solution.name + "\n\nですか?"
            save_status(user_status, GameState.GUESSING)
            reply_content.append(QuickMessageForm(text=reply_text, items=["はい", "いいえ"]))
    else:
        reply_content.append(TextMessageForm(text="Pardon?"))
    return reply_content

def handle_guessing(user_status, message):
    reply_content = []
    if message == "はい":
        reply_content.append(TextMessageForm(text="やったー"))
        update_features(user_status.progress)
        reset_status(user_status)
    elif message == "いいえ":
        reply_content.append(TextMessageForm(text="ええ〜"))
        reply_content.append(QuickMessageForm(text="続けますか?", items=["はい", "いいえ"]))
        save_status(user_status, GameState.RESUMING)
    else:
        reply_content.append(TextMessageForm(text="Pardon?"))
    return reply_content

def handle_resuming(user_status, message):
    reply_content = []
    if message == "はい":
        user_status.progress.candidates = Solution.query.all()
        question = select_next_question(user_status.progress)
        reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
        save_status(user_status, GameState.ASKING, question)
    elif message == "いいえ":
        reply_content.append(TextMessageForm(text="そっすか〜…"))
        # items must not be more than 13.
        items = [s.name for s in user_status.progress.candidates][:12] + ["どれも当てはまらない"]
        reply_content.append(QuickMessageForm(text="当てはまるものを選んでください", items=items))
        save_status(user_status, GameState.BEGGING)
    else:
        reply_content.append(TextMessageForm(text="Pardon?"))
    return reply_content

def handle_begging(user_status, message):
    reply_content = []
    if message in [s.name for s in Solution.query.all()]:
        true_solution = Solution.query.filter_by(name=message).first()
        update_features(user_status.progress, true_solution)
        reset_status(user_status)
        save_status(user_status, GameState.PENDING)
        reply_content.append(TextMessageForm(text="なるほど，勉強になります．"))
    elif message == "どれも当てはまらない":
        save_status(user_status, GameState.REGISTERING)
        reply_content.append(TextMessageForm(text="答えを入力してくださいな…"))
    else:
        reply_content.append(TextMessageForm(text="なにそれは…"))
        items = [s.name for s in user_status.progress.candidates] + ["どれも当てはまらない"]
        reply_content.append(QuickMessageForm(text="当てはまるものを選んでください", items=items))
    return reply_content


def handle_registering(user_status, message):
    reply_content = []
    prepared_solution = PreparedSolution()
    prepared_solution.name = message
    user_status.progress.prepared_solution = prepared_solution
    save_status(user_status, GameState.CONFIRMING)
    confirm_text = "思い浮かべていたのは\n\n" + message + "\n"
    reply_content.append(TextMessageForm(text=confirm_text))
    reply_content.append(QuickMessageForm(text="…でよろしいですか？", items=["はい", "いいえ"]))
    return reply_content

def handle_confirming(user_status, message):
    reply_content = []
    pre_solution = user_status.progress.prepared_solution
    name = pre_solution.name
    if message == "はい":
        db.session.delete(pre_solution)
        db.session.commit()
        new_solution = Solution()
        new_solution.name = name
        db.session.add(new_solution)
        db.session.commit()
        update_features(user_status.progress, new_solution)
        text = name + "ですね．\n覚えておきます．"
        reply_content.append(TextMessageForm(text=text))
        save_status(user_status, GameState.FEATURING)
        text = "最後に，\n" + name + "には当てはまって，\n" \
             + user_status.progress.candidates[0].name + "には当てはまらないような\n質問を入力してください"
        reply_content.append(TextMessageForm(text=text))
    elif message == "いいえ":
        db.session.delete(pre_solution)
        db.session.commit()
        save_status(user_status, GameState.REGISTERING)
        reply_content.append(TextMessageForm(text="おっと"))
        reply_content.append(TextMessageForm(text="もう一度答えを入力してください"))
    else:
        reply_content.append(TextMessageForm(text="ええ…"))
        confirm_text = "思い浮かべていたのは\n\n" + name + "\n\nでよろしいですか？"
        reply_content.append(QuickMessageForm(text=confirm_text, items=["はい", "いいえ"]))
    return reply_content

def handle_training(user_status, message):
    pass

def handle_featuring(user_status, message):
    reply_content = []
    reset_status(user_status)
    save_status(user_status, GameState.PENDING)
    reply_content.append(TextMessageForm(text=message))
    return reply_content

def handle_labeling(user_status, message):
    pass

def handle_updating(user_status, message):
    pass
