from tanakinator import line, handler, db
from tanakinator.models import UserStatus
from tanakinator.akinator import GameState, get_game_status

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    user_id = event.source.user_id

    reply_text = []
    if message in [state.value for state in GameState]:
        current_status = get_game_status(user_id)
        next_status = GameState(message)
        reply_text.append(current_status.value + " -> " + next_status.value)
        user_status = db.session.query(UserStatus).filter_by(user_id=user_id).first()
        user_status.status = next_status.value
        db.session.add(user_status)
        db.session.commit()

    reply_text.append("Choose next game-status.")
    items = [
        QuickReplyButton(action=MessageAction(label="PENDING", text="pending")),
        QuickReplyButton(action=MessageAction(label="ASKING", text="asking")),
        QuickReplyButton(action=MessageAction(label="GUESSING", text="guessing"))
    ]
    reply_content = TextSendMessage(text=reply_text, quick_reply=QuickReply(items=items))

    line.reply_message(event.reply_token, reply_content)
