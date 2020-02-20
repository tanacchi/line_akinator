from tanakinator import line, handler, db
from tanakinator.models import LatestMessage

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text

    user_id = event.source.user_id
    latest = db.session.query(LatestMessage).filter_by(user_id=user_id).first()
    if latest:
        latest.message = message[:200]
    else:
        latest = LatestMessage(user_id, message)
    db.session.add(latest)
    db.session.commit()

    if message == "Play now.":
        reply_content = TextSendMessage(text="Hello.")
    else:
        items = [
            QuickReplyButton(action=MessageAction(label="Play now", text="Play now."))
        ]
        reply_content = TextSendMessage(text="Ready?", quick_reply=QuickReply(items=items))

    line.reply_message(event.reply_token, reply_content)
