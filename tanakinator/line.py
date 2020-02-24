from tanakinator import line, handler, db
from tanakinator.common import GameState, TextMessageForm, QuickMessageForm
from tanakinator.akinator import (
    get_user_status, handle_pending, handle_asking,
    handle_guessing
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


akinator_handler_table = {
    GameState.PENDING:     handle_pending,
    GameState.ASKING:      handle_asking,
    GameState.GUESSING:    handle_guessing
}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    user_id = event.source.user_id

    user_status = get_user_status(user_id)
    status = GameState(user_status.status)
    akinator_handler = akinator_handler_table.get(status)

    reply_content = akinator_handler(user_status, message)
    reply_content = convert_form_to_message(reply_content)
    line.reply_message(event.reply_token, reply_content)
