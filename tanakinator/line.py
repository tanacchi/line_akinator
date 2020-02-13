from tanakinator import line, handler

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "Play now.":
        reply_content = TextSendMessage(text="Hello.")
    else:
        items = [
            QuickReplyButton(action=MessageAction(label="Play now", text="Play now."))
        ]
        reply_content = TextSendMessage(quick_reply=QuickReply(items=items))

    line.reply_message(event.reply_token, reply_content)
