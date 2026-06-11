from datetime import datetime
from app import db


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    start_date = db.Column(db.String(20), default='')
    end_date = db.Column(db.String(20), default='')
    location = db.Column(db.String(200), default='')
    category = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    games = db.relationship('Game', backref=db.backref('tournament', lazy='select'), lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'category': self.category,
            'game_count': self.games.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Tournament {self.name}>'
