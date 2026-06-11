from datetime import datetime
from app import db


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    title = db.Column(db.String(10), default='', comment='GM/IM/FM/WGM等')
    country = db.Column(db.String(100), default='', index=True)
    elo_rating = db.Column(db.Integer, default=0, index=True)
    birth_date = db.Column(db.String(20), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    white_games = db.relationship('Game', foreign_keys='Game.white_player_id', backref=db.backref('white_player', lazy='select'), lazy='dynamic')
    black_games = db.relationship('Game', foreign_keys='Game.black_player_id', backref=db.backref('black_player', lazy='select'), lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'country': self.country,
            'elo_rating': self.elo_rating,
            'birth_date': self.birth_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def get_stats(self):
        white_wins = self.white_games.filter_by(result='1-0').count()
        white_losses = self.white_games.filter_by(result='0-1').count()
        white_draws = self.white_games.filter_by(result='1/2-1/2').count()
        black_wins = self.black_games.filter_by(result='0-1').count()
        black_losses = self.black_games.filter_by(result='1-0').count()
        black_draws = self.black_games.filter_by(result='1/2-1/2').count()
        total = white_wins + white_losses + white_draws + black_wins + black_losses + black_draws
        wins = white_wins + black_wins
        return {
            'total_games': total,
            'wins': wins,
            'losses': white_losses + black_losses,
            'draws': white_draws + black_draws,
            'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
            'as_white': {'wins': white_wins, 'losses': white_losses, 'draws': white_draws},
            'as_black': {'wins': black_wins, 'losses': black_losses, 'draws': black_draws},
        }

    def __repr__(self):
        return f'<Player {self.name} ({self.title}) elo={self.elo_rating}>'
