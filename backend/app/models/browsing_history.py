from datetime import datetime
from app import db


class BrowsingHistory(db.Model):
    __tablename__ = 'browsing_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    game = db.relationship('Game', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id', name='uq_user_game_browse'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
        }
