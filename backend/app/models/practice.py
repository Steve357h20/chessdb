import json
from datetime import datetime
from app import db


class Puzzle(db.Model):
    __tablename__ = 'puzzles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    puzzle_number = db.Column(db.Integer, unique=True, nullable=True, index=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='endgame')
    difficulty = db.Column(db.String(20), default='medium')
    description = db.Column(db.Text, default='')
    hint = db.Column(db.Text, default='')
    fen = db.Column(db.Text, nullable=False)
    source_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True, index=True)
    from_move = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    is_preset = db.Column(db.Boolean, default=False, index=True)
    practice_count = db.Column(db.Integer, default=0)
    solve_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    source_game = db.relationship('Game', backref='puzzles', lazy='select')
    creator = db.relationship('User', backref='created_puzzles', lazy='select')

    def assign_puzzle_number(self):
        if self.puzzle_number is not None:
            return
        if self.is_preset:
            max_num = db.session.query(db.func.max(Puzzle.puzzle_number)).scalar() or 0
            self.puzzle_number = max_num + 1 if max_num < 1000 else max_num + 1
        else:
            max_num = db.session.query(db.func.max(Puzzle.puzzle_number)).scalar() or 0
            self.puzzle_number = max(max_num + 1, 1001)

    def to_dict(self, include_source=False):
        data = {
            'id': self.id,
            'puzzle_number': self.puzzle_number,
            'name': self.name,
            'category': self.category,
            'difficulty': self.difficulty,
            'description': self.description,
            'hint': self.hint,
            'fen': self.fen,
            'source_game_id': self.source_game_id,
            'from_move': self.from_move,
            'created_by': self.created_by,
            'is_preset': self.is_preset,
            'practice_count': self.practice_count,
            'solve_count': self.solve_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_source and self.source_game:
            data['source_game'] = {
                'id': self.source_game.id,
                'white_player_name': self.source_game.white_player.name if self.source_game.white_player else '?',
                'black_player_name': self.source_game.black_player.name if self.source_game.black_player else '?',
                'result': self.source_game.result,
                'date': self.source_game.date,
            }
        return data

    def __repr__(self):
        return f'<Puzzle {self.id} {self.name}>'


class PracticeGame(db.Model):
    __tablename__ = 'practice_games'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    mode = db.Column(db.String(20), nullable=False, comment='puzzle/from_game/custom')
    puzzle_id = db.Column(db.Integer, db.ForeignKey('puzzles.id'), nullable=True, index=True)
    source_game_id = db.Column(db.Integer, nullable=True)
    from_move = db.Column(db.Integer, nullable=True)
    start_fen = db.Column(db.Text, default='')
    user_color = db.Column(db.String(1), default='w')
    difficulty = db.Column(db.String(20), default='medium')
    moves_json = db.Column(db.Text, default='[]')
    final_fen = db.Column(db.Text, default='')
    result = db.Column(db.String(10), default='*')
    total_moves = db.Column(db.Integer, default=0)
    hints_used = db.Column(db.Integer, default=0)
    undo_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer, nullable=True)
    analysis_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='practice_games', lazy='select')
    puzzle = db.relationship('Puzzle', backref='practice_games', lazy='select')

    def to_dict(self):
        moves = []
        if self.moves_json:
            try:
                moves = json.loads(self.moves_json)
            except (json.JSONDecodeError, TypeError):
                moves = []

        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'mode': self.mode,
            'puzzle_id': self.puzzle_id,
            'source_game_id': self.source_game_id,
            'from_move': self.from_move,
            'start_fen': self.start_fen,
            'user_color': self.user_color,
            'difficulty': self.difficulty,
            'moves': moves,
            'final_fen': self.final_fen,
            'result': self.result,
            'total_moves': self.total_moves,
            'hints_used': self.hints_used,
            'undo_count': self.undo_count,
            'duration_seconds': self.duration_seconds,
            'has_analysis': bool(self.analysis_json),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<PracticeGame {self.id} mode={self.mode} result={self.result}>'
