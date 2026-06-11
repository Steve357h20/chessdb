from app import db


class Opening(db.Model):
    __tablename__ = 'openings'
    id = db.Column(db.Integer, primary_key=True)
    eco_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    variation = db.Column(db.String(100), default='')
    moves = db.Column(db.Text, default='[]')
    category = db.Column(db.String(1), default='A', index=True)
    description = db.Column(db.Text, default='')
    popularity = db.Column(db.Integer, default=0)
    white_win_rate = db.Column(db.Float, default=50.0)
    black_win_rate = db.Column(db.Float, default=50.0)
    draw_rate = db.Column(db.Float, default=0.0)

    def get_moves_list(self):
        import json
        try:
            return json.loads(self.moves)
        except:
            return []

    def to_dict(self):
        return {
            'eco_code': self.eco_code, 'name': self.name,
            'variation': self.variation, 'moves': self.get_moves_list(),
            'category': self.category, 'description': self.description,
            'popularity': self.popularity, 'white_win_rate': self.white_win_rate,
            'black_win_rate': self.black_win_rate, 'draw_rate': self.draw_rate,
        }
