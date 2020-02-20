from tanakinator import db


class LatestMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False, unique=True)
    message = db.Column(db.String(200), nullable=False)

    def __init__(self, user_id, message):
        self.user_id = user_id
        self.message = message


def init():
    db.create_all()
