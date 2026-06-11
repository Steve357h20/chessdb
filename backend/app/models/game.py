import json
from datetime import datetime
from app import db


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_number = db.Column(db.Integer, unique=True, nullable=True, index=True)
    white_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    black_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True, index=True)
    date = db.Column(db.String(20), default='', index=True)
    result = db.Column(db.String(10), default='*', comment='1-0/0-1/1/2-1/2/*')
    pgn_content = db.Column(db.Text, default='')
    eco_code = db.Column(db.String(10), default='', index=True)
    opening_name = db.Column(db.String(200), default='')
    total_moves = db.Column(db.Integer, default=0)
    final_fen = db.Column(db.String(100), default='')
    white_elo = db.Column(db.Integer, nullable=True)
    black_elo = db.Column(db.Integer, nullable=True)
    termination = db.Column(db.String(50), default='', comment='Normal/Time forfeit/Abandoned/etc')
    time_control = db.Column(db.String(30), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    analysis = db.relationship('Analysis', backref='game', lazy='select', uselist=False)
    collections = db.relationship('Collection', backref='game', lazy='dynamic')

    def assign_game_number(self):
        if self.game_number is not None:
            return
        max_num = db.session.query(db.func.max(Game.game_number)).scalar() or 0
        self.game_number = max_num + 1

    def to_dict(self):
        return {
            'id': self.id,
            'game_number': self.game_number,
            'white_player_id': self.white_player_id,
            'black_player_id': self.black_player_id,
            'white_player_name': self.white_player.name if self.white_player else '',
            'black_player_name': self.black_player.name if self.black_player else '',
            'white_elo': self.white_elo,
            'black_elo': self.black_elo,
            'tournament_id': self.tournament_id,
            'tournament_name': self.tournament.name if self.tournament else '',
            'date': self.date,
            'result': self.result,
            'eco_code': self.eco_code,
            'opening_name': self.opening_name,
            'total_moves': self.total_moves,
            'final_fen': self.final_fen,
            'termination': self.termination,
            'time_control': self.time_control,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def get_moves_list(self):
        if not self.pgn_content:
            return []
        try:
            import chess.pgn
            from io import StringIO
            game_obj = chess.pgn.read_game(StringIO(self.pgn_content))
            if game_obj is None:
                return []
            moves = []
            node = game_obj
            move_number = 0
            while node.variations:
                next_node = node.variation(0)
                move = next_node.move
                san = node.board().san(move)
                fen_before = node.board().fen()
                fen_after = next_node.board().fen()
                if node.board().turn:
                    move_number += 1
                moves.append({
                    'move_number': move_number,
                    'san': san,
                    'uci': move.uci(),
                    'fen_before': fen_before,
                    'fen_after': fen_after,
                    'color': 'w' if node.board().turn else 'b',
                })
                node = next_node
            return moves
        except Exception:
            return []

    def __repr__(self):
        return f'<Game {self.id} {self.white_player.name if self.white_player else "?"} vs {self.black_player.name if self.black_player else "?"} {self.result}>'
