import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.opening import Opening
from app.models.game import Game
from sqlalchemy import func


def import_openings():
    app = create_app()
    with app.app_context():
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'openings_standard.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            openings_data = json.load(f)

        print(f"Loaded {len(openings_data)} openings from JSON")

        Opening.query.delete()
        db.session.commit()
        print("Cleared existing openings")

        for eco_code, info in sorted(openings_data.items()):
            category = eco_code[0]
            opening = Opening(
                eco_code=eco_code,
                name=info.get('name', ''),
                variation=info.get('variation', ''),
                moves=json.dumps(info.get('moves', []), ensure_ascii=False),
                category=category,
                description=info.get('description', ''),
                popularity=0,
                white_win_rate=50.0,
                black_win_rate=50.0,
                draw_rate=0.0,
            )
            db.session.add(opening)

        db.session.commit()
        print(f"Imported {len(openings_data)} openings")

        eco_stats = db.session.query(
            Game.eco_code,
            func.count(Game.id).label('total'),
            func.sum(func.iif(Game.result == '1-0', 1, 0)).label('white_wins'),
            func.sum(func.iif(Game.result == '0-1', 1, 0)).label('black_wins'),
            func.sum(func.iif(Game.result == '1/2-1/2', 1, 0)).label('draws'),
        ).filter(
            Game.eco_code != None,
            Game.eco_code != '',
        ).group_by(Game.eco_code).all()

        updated = 0
        for stat in eco_stats:
            eco = stat.eco_code
            if not eco:
                continue
            opening = Opening.query.filter(Opening.eco_code == eco).first()
            if not opening:
                continue
            total = stat.total or 0
            if total == 0:
                continue
            white_wins = stat.white_wins or 0
            black_wins = stat.black_wins or 0
            draws = stat.draws or 0
            opening.white_win_rate = round(white_wins / total * 100, 1)
            opening.black_win_rate = round(black_wins / total * 100, 1)
            opening.draw_rate = round(draws / total * 100, 1)
            opening.popularity = total
            updated += 1

        db.session.commit()
        print(f"Updated win rates for {updated} openings from game data")

        total_openings = Opening.query.count()
        print(f"Total openings in database: {total_openings}")


if __name__ == '__main__':
    import_openings()
