from tanakinator import line, handler, db
from tanakinator.models import (
    UserStatus, Question, Progress,
    Answer, Solution, Feature
)
from tanakinator.akinator import (
    GameState, get_game_status, get_user_status,
    select_next_question, save_status, can_guess,
    push_answer, guess_solution
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


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
            items = [
                QuickReplyButton(action=MessageAction(label="はい", text="はい")),
                QuickReplyButton(action=MessageAction(label="いいえ", text="いいえ")),
            ]
            reply_content.append(TextSendMessage(text=question.message, quick_reply=QuickReply(items=items)))

        else:
            reply_text = "「はじめる」をタップ！"
            items = [
                QuickReplyButton(action=MessageAction(label="はじめる", text="はじめる")),
            ]
            reply_content.append(TextSendMessage(text=reply_text, quick_reply=QuickReply(items=items)))

    elif status == GameState.ASKING:
        if message in ["はい", "いいえ"]:
            push_answer(user_status.progress, message)
            if not can_guess(user_status.progress):
                question = select_next_question(user_status.progress)
                save_status(user_status, next_question=question)
                items = [
                    QuickReplyButton(action=MessageAction(label="はい", text="はい")),
                    QuickReplyButton(action=MessageAction(label="いいえ", text="いいえ")),
                ]
                reply_content.append(TextSendMessage(text=question.message, quick_reply=QuickReply(items=items)))
            else:
                most_likely_solution = guess_solution(user_status.progress)
                reply_text = "思い浮かべているのは\n\n" + most_likely_solution.name + "\n\nですか?"
                items = [
                    QuickReplyButton(action=MessageAction(label="はい", text="はい")),
                    QuickReplyButton(action=MessageAction(label="いいえ", text="いいえ")),
                ]
                reply_content.append(TextSendMessage(text=reply_text, quick_reply=QuickReply(items=items)))
                save_status(user_status, GameState.GUESSING)
        else:
            reply_text = "Pardon?"
            reply_content.append(TextSendMessage(text=reply_text))

    elif status == GameState.GUESSING:
        if message in ["はい", "いいえ"]:
            reply_text = "やったー" if message == "はい" else "ええ〜"
            db.session.query(Answer).filter_by(progress_id=user_status.progress.id).delete()
            db.session.delete(user_status.progress)
            save_status(user_status, GameState.PENDING)
        else:
            reply_text = "Pardon?"
        reply_content.append(TextSendMessage(text=reply_text))

    line.reply_message(event.reply_token, reply_content)
