PUZZLE_LIBRARY = {
    'endgame_king_pawn': {
        'name': '王兵残局',
        'category': 'endgame',
        'difficulty': 'beginner',
        'description': '白方王和兵对抗黑方王，练习推动兵升变的基本技巧',
        'fen': '8/8/8/8/4k3/8/4P3/4K3 w - - 0 1',
        'hint': '用王保护兵前进，逐步推进兵升变',
    },
    'endgame_rook': {
        'name': '车杀残局',
        'category': 'endgame',
        'difficulty': 'easy',
        'description': '白方车和王对抗黑方王和兵，练习用车将杀的基本方法',
        'fen': '6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1',
        'hint': '用车切断黑王逃跑路线，配合己方王逐步逼近将杀',
    },
    'endgame_queen_vs_rook': {
        'name': '后对车',
        'category': 'endgame',
        'difficulty': 'medium',
        'description': '黑方后对白方王，练习用后将杀的技巧',
        'fen': '8/8/4k3/8/8/4K3/8/3q4 w - - 0 1',
        'hint': '白方需谨慎防守，黑方利用后的灵活性逐步逼近将杀',
    },
    'tactic_fork': {
        'name': '骑士叉击',
        'category': 'tactics',
        'difficulty': 'easy',
        'description': '经典学者将杀局面，白方后和象配合攻击f7弱格',
        'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
        'hint': '后h5配合象c4攻击f7弱格，尝试将杀或赢得子力',
    },
    'tactic_pin': {
        'name': '牵制战术',
        'category': 'tactics',
        'difficulty': 'medium',
        'description': '意大利开局局面，练习识别和利用牵制关系',
        'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
        'hint': '注意d5和f7的牵制可能性，利用象和后的配合',
    },
    'tactic_discovered_attack': {
        'name': '闪击战术',
        'category': 'tactics',
        'difficulty': 'hard',
        'description': '复杂的中局局面，需要发现闪击机会赢得子力优势',
        'fen': 'r1bqk2r/pppp1ppp/2n2n2/4p3/2B1P1b1/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
        'hint': '移动一个子力露出后面子力的攻击线，创造双重威胁',
    },
    'opening_scholar_mate': {
        'name': '学者将杀',
        'category': 'mate',
        'difficulty': 'beginner',
        'description': '经典学者将杀，黑方需防守f7弱格避免快速被将杀',
        'fen': 'r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3',
        'hint': '黑方需要防守f7格，考虑走g6或Qe7阻挡后的攻击',
    },
    'endgame_bishop_pair': {
        'name': '双象残局',
        'category': 'endgame',
        'difficulty': 'hard',
        'description': '白方双象对抗黑方王，练习双象配合将杀的高级技巧',
        'fen': '8/8/4k3/8/8/2B1K3/4B3/8 w - - 0 1',
        'hint': '双象配合将王逼到角落，利用不同色格象封锁王的出路',
    },
    'mate_in_two_1': {
        'name': '两步将杀',
        'category': 'mate',
        'difficulty': 'medium',
        'description': '白方车和王配合，两步内将杀黑方王',
        'fen': '6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1',
        'hint': '用车将军将黑王逼到边线，然后配合王完成将杀',
    },
    'mate_in_two_2': {
        'name': '后翼将杀',
        'category': 'mate',
        'difficulty': 'easy',
        'description': '利用后的力量在王翼发起攻击，寻找将杀机会',
        'fen': '5rk1/pp3ppp/2p5/3n4/8/1P1BQ3/1BPP1PPP/R3K2R w KQ - 0 1',
        'hint': '后和象配合攻击黑方王翼，寻找打开h线的将杀机会',
    },
}


def get_all_puzzles() -> dict:
    return dict(PUZZLE_LIBRARY)


def get_puzzles_by_category(category: str) -> dict:
    return {k: v for k, v in PUZZLE_LIBRARY.items() if v['category'] == category}


def get_puzzles_by_difficulty(difficulty: str) -> dict:
    return {k: v for k, v in PUZZLE_LIBRARY.items() if v['difficulty'] == difficulty}


def get_puzzle(puzzle_id: str) -> dict:
    return PUZZLE_LIBRARY.get(puzzle_id)


def init_system_puzzles():
    from app import db
    from app.models.practice import Puzzle

    existing = Puzzle.query.filter_by(is_preset=True).count()
    if existing > 0:
        return

    for key, data in PUZZLE_LIBRARY.items():
        puzzle = Puzzle(
            name=data['name'],
            category=data['category'],
            difficulty=data['difficulty'],
            description=data.get('description', ''),
            hint=data.get('hint', ''),
            fen=data['fen'],
            is_preset=True,
        )
        puzzle.assign_puzzle_number()
        db.session.add(puzzle)

    db.session.commit()
