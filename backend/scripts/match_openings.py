import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.game import Game
from app.services.opening_recognizer import OpeningRecognizer


def match_openings():
    app = create_app()

    with app.app_context():
        recognizer = OpeningRecognizer()

        games = Game.query.filter(db.or_(Game.eco_code == None, Game.eco_code == '')).all()
        total = len(games)
        print(f'Found {total} games without eco_code')

        updated = 0
        for i, game in enumerate(games):
            moves = game.get_moves_list()
            if not moves:
                continue

            san_moves = []
            for m in moves:
                if m.get('white'):
                    san_moves.append(m['white'])
                if m.get('black'):
                    san_moves.append(m['black'])

            if not san_moves:
                continue

            result = recognizer.identify_opening(san_moves)
            if result and result.get('eco_code'):
                game.eco_code = result['eco_code']
                game.opening_name = result['name']
                updated += 1

            if (i + 1) % 100 == 0:
                db.session.commit()
                print(f'Processed {i + 1}/{total}, updated {updated}')

        db.session.commit()
        print(f'Done. Total processed: {total}, updated: {updated}')


if __name__ == '__main__':
    match_openings()
