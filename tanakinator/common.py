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
