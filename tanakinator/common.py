import enum


class GameState(enum.Enum):
    PENDING     = 'pending'
    ASKING      = 'asking'
    GUESSING    = 'guessing'
    RESUMING    = 'resuming'
    BEGGING     = 'begging'
    REGISTERING = 'registering'
    CONFIRMING  = 'confirming'
    TRAINING    = 'training'
    FEATURING   = 'featuring'
    LABELING    = 'labeling'
    UPDATING    = 'updating'

class TextMessageForm(object):
    def __init__(self, text, items=None):
        self.text = text

class QuickMessageForm(object):
    def __init__(self, text, items=None):
        self.text = text
        self.items = items
