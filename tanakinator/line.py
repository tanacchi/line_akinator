from tanakinator import line, handler, db
from tanakinator.models import UserStatus, Question, Progress
from tanakinator.akinator import GameState, get_game_status

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    user_id = event.source.user_id
    reply_content = []

    if message == "はじめる":
        user_status = db.session.query(UserStatus).filter_by(user_id=user_id).first()
        if not user_status:
            user_status = UserStatus()
            user_status.user_id = user_id
        question = Question.query.all()[0]
        user_status.progress = Progress()
        user_status.progress.latest_question = question
        user_status.status = GameState.ASKING.value
        db.session.add(user_status)
        db.session.commit()
        items = [
            QuickReplyButton(action=MessageAction(label="はい", text="はい")),
            QuickReplyButton(action=MessageAction(label="いいえ", text="いいえ")),
        ]
        reply_content.append(TextSendMessage(text=question.message, quick_reply=QuickReply(items=items)))

    else:
        reply_text = "Pardon?"
        reply_content.append(TextSendMessage(text=reply_text))

    line.reply_message(event.reply_token, reply_content)
