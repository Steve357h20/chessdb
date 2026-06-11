import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.opening import Opening


def import_openings(json_path):
    app = create_app()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with app.app_context():
        added = 0
        updated = 0
        count = 0

        for eco_code, info in data.items():
            existing = Opening.query.filter_by(eco_code=eco_code).first()

            if existing:
                existing.name = info.get('name', existing.name)
                existing.variation = info.get('variation', existing.variation)
                existing.moves = json.dumps(info.get('moves', []), ensure_ascii=False)
                existing.category = eco_code[0] if eco_code else 'A'
                existing.description = info.get('description', existing.description)
                updated += 1
            else:
                opening = Opening(
                    eco_code=eco_code,
                    name=info.get('name', ''),
                    variation=info.get('variation', ''),
                    moves=json.dumps(info.get('moves', []), ensure_ascii=False),
                    category=eco_code[0] if eco_code else 'A',
                    description=info.get('description', ''),
                )
                db.session.add(opening)
                added += 1

            count += 1
            if count % 100 == 0:
                db.session.commit()

        db.session.commit()
        print(f'新增{added}条，更新{updated}条')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/import_openings.py data/openings.json')
        sys.exit(1)
    import_openings(sys.argv[1])
