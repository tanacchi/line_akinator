from flask import url_for
from tanakinator import line, handler, db
from tanakinator.common import (
    GameState, TextMessageForm, QuickMessageForm,
    RefToSolutionForm
)
from tanakinator.akinator import (
    get_user_status, handle_pending, handle_asking,
    handle_guessing, handle_resuming, handle_begging,
    handle_registering, handle_confirming, handle_training,
    handle_featuring, handle_labeling, handle_updating
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    URIAction
)


def convert_form_to_message(form_list):
    reply_content = []
    for form in form_list:
        if isinstance(form, TextMessageForm):
            message = TextSendMessage(text=form.text)
        elif isinstance(form, QuickMessageForm):
            items = [QuickReplyButton(action=MessageAction(label=item, text=item)) for item in form.items]
            message = TextSendMessage(text=form.text, quick_reply=QuickReply(items=items))
        elif isinstance(form, RefToSolutionForm):
            uri = f"https://tanakinator.herokuapp.com/solutions/{form.s_id}/edit"
            items = [
                QuickReplyButton(action=URIAction(label="いいよ", uri=uri)),
                QuickReplyButton(action=MessageAction(label="いやだ", text="See ya!"))
            ]
            message = TextSendMessage(text=form.text, quick_reply=QuickReply(items=items))
        reply_content.append(message)
    return reply_content


akinator_handler_table = {
    GameState.PENDING:     handle_pending,
    GameState.ASKING:      handle_asking,
    GameState.GUESSING:    handle_guessing,
    GameState.RESUMING:    handle_resuming,
    GameState.BEGGING:     handle_begging,
    GameState.REGISTERING: handle_registering,
    GameState.CONFIRMING:  handle_confirming,
    GameState.TRAINING:    handle_training,
    GameState.FEATURING:   handle_featuring,
    GameState.LABELING:    handle_labeling,
    GameState.UPDATING:    handle_updating,
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
