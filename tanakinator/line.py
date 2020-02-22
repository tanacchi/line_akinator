from tanakinator import line, handler, db
from tanakinator.common import GameState, TextMessageForm, QuickMessageForm
from tanakinator.models import (
    UserStatus, Question, Progress,
    Answer, Solution, Feature
)
from tanakinator.akinator import (
    get_game_status, get_user_status,
    select_next_question, save_status, can_guess,
    push_answer, guess_solution
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


def convert_form_to_message(form_list):
    reply_content = []
    for form in form_list:
        if isinstance(form, TextMessageForm):
            message = TextSendMessage(text=form.text)
        elif isinstance(form, QuickMessageForm):
            items = [QuickReplyButton(action=MessageAction(label=item, text=item)) for item in form.items]
            message = TextSendMessage(text=form.text, quick_reply=QuickReply(items=items))
        reply_content.append(message)
    return reply_content


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    user_id = event.source.user_id
    reply_content = []

    user_status = get_user_status(user_id)
    status = GameState(user_status.status)

    if status == GameState.PENDING:
        if message == "はじめる":
            user_status.progress = Progress()
            question = select_next_question(user_status.progress)
            save_status(user_status, GameState.ASKING, question)
            reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
        else:
            reply_content.append(QuickMessageForm(text="「はじめる」をタップ！", items=["はじめる"]))

    elif status == GameState.ASKING:
        if message in ["はい", "いいえ"]:
            push_answer(user_status.progress, message)
            if not can_guess(user_status.progress):
                question = select_next_question(user_status.progress)
                save_status(user_status, next_question=question)
                reply_content.append(QuickMessageForm(text=question.message, items=["はい", "いいえ"]))
            else:
                most_likely_solution = guess_solution(user_status.progress)
                reply_text = "思い浮かべているのは\n\n" + most_likely_solution.name + "\n\nですか?"
                reply_content.append(QuickMessageForm(text=reply_text, items=["はい", "いいえ"]))
                save_status(user_status, GameState.GUESSING)
        else:
            reply_content.append(TextMessageForm(text="Pardon?"))

    elif status == GameState.GUESSING:
        if message in ["はい", "いいえ"]:
            reply_text = "やったー" if message == "はい" else "ええ〜"
            db.session.query(Answer).filter_by(progress_id=user_status.progress.id).delete()
            db.session.delete(user_status.progress)
            save_status(user_status, GameState.PENDING)
        else:
            reply_text = "Pardon?"
        reply_content.append(TextMessageForm(text=reply_text))

    reply_content = convert_form_to_message(reply_content)
    line.reply_message(event.reply_token, reply_content)
