import os
import json
import click
from flask import current_app
from app import create_app, db
from app.models import Player, Game, Tournament, Analysis, Opening, User, Collection

OPENINGS_DATA = [
    {'eco_code': 'A01', 'name': 'Nimzovich-Larsen Attack', 'variation': '1.b3', 'moves': ['b3'], 'description': '以侧翼兵起步的灵活开局，由尼姆佐维奇和拉尔森推广', 'category': 'A'},
    {'eco_code': 'A04', 'name': "Reti Opening", 'variation': '1.Nf3', 'moves': ['Nf3'], 'description': '以骑士起步的超现代开局，控制中心而非直接占领', 'category': 'A'},
    {'eco_code': 'A07', 'name': "King's Indian Attack", 'variation': '1.Nf3 d5 2.g3', 'moves': ['Nf3', 'd5', 'g3'], 'description': '白方采用国王印度防御阵型的反向开局', 'category': 'A'},
    {'eco_code': 'A22', 'name': 'English Opening: Four Knights', 'variation': '1.c4 e5 2.Nc3 Nf6 3.Nf3 Nc6', 'moves': ['c4', 'e5', 'Nc3', 'Nf6', 'Nf3', 'Nc6'], 'description': '英国开局中的四骑士变例', 'category': 'A'},
    {'eco_code': 'B20', 'name': 'Sicilian Defense', 'variation': '1.e4 c5', 'moves': ['e4', 'c5'], 'description': '黑方最流行的应对1.e4的开局，以不对称局面争取胜利', 'category': 'B'},
    {'eco_code': 'B33', 'name': 'Sveshnikov Variation', 'variation': '1.e4 c5 2.Nf3 Nc6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 e5', 'moves': ['e4', 'c5', 'Nf3', 'Nc6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'e5'], 'description': '西西里防御中最尖锐的变例之一，斯韦什尼科夫变例', 'category': 'B'},
    {'eco_code': 'B40', 'name': 'Sicilian Defense: French Variation', 'variation': '1.e4 c5 2.Nf3 e6', 'moves': ['e4', 'c5', 'Nf3', 'e6'], 'description': '西西里-法兰西混合体系', 'category': 'B'},
    {'eco_code': 'B90', 'name': 'Sicilian Najdorf', 'variation': '1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6', 'moves': ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'a6'], 'description': '西西里纳伊多夫变例，当今最高水平的首选开局之一', 'category': 'B'},
    {'eco_code': 'C42', 'name': "Petrov's Defense", 'variation': '1.e4 e5 2.Nf3 Nf6', 'moves': ['e4', 'e5', 'Nf3', 'Nf6'], 'description': '俄罗斯防御，以反击代替防守的开局', 'category': 'C'},
    {'eco_code': 'C50', 'name': 'Giuoco Piano', 'variation': '1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5', 'moves': ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5'], 'description': '意大利开局，最古老的开局之一', 'category': 'C'},
    {'eco_code': 'C55', 'name': 'Two Knights Defense', 'variation': '1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6', 'moves': ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Nf6'], 'description': '双骑士防御，意大利开局中的尖锐变例', 'category': 'C'},
    {'eco_code': 'C67', 'name': "Ruy Lopez: Berlin Defense", 'variation': '1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6', 'moves': ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'Nf6'], 'description': '西班牙开局柏林防御，被称为柏林墙', 'category': 'C'},
    {'eco_code': 'C84', 'name': "Ruy Lopez: Closed", 'variation': '1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7', 'moves': ['e4', 'e5', 'Nf3', 'Nc6', 'Bb5', 'a6', 'Ba4', 'Nf6', 'O-O', 'Be7'], 'description': '西班牙开局封闭变例，最经典的局面型开局', 'category': 'C'},
    {'eco_code': 'D35', 'name': "Queen's Gambit Declined", 'variation': '1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.cxd5 exd5', 'moves': ['d4', 'd5', 'c4', 'e6', 'Nc3', 'Nf6', 'cxd5', 'exd5'], 'description': '后翼弃兵拒吃变例，最稳固的应对之一', 'category': 'D'},
    {'eco_code': 'D37', 'name': "QGD: 4.Nc3", 'variation': '1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Nf3', 'moves': ['d4', 'd5', 'c4', 'e6', 'Nc3', 'Nf6', 'Nf3'], 'description': '后翼弃兵拒吃：骑士发展变例', 'category': 'D'},
    {'eco_code': 'D44', 'name': "Semi-Slav Defense", 'variation': '1.d4 d5 2.c4 c6 3.Nf3 Nf6 4.Nc3 e6 5.Bg5 dxc4', 'moves': ['d4', 'd5', 'c4', 'c6', 'Nf3', 'Nf6', 'Nc3', 'e6', 'Bg5', 'dxc4'], 'description': '半斯拉夫防御，结合斯拉夫和拒弃兵的思路', 'category': 'D'},
    {'eco_code': 'D85', 'name': "Grünfeld Defense", 'variation': '1.d4 Nf6 2.c4 g6 3.Nc3 d5', 'moves': ['d4', 'Nf6', 'c4', 'g6', 'Nc3', 'd5'], 'description': '格林菲尔德防御，以让出中心后反击为特征', 'category': 'D'},
    {'eco_code': 'E15', "name": "Queen's Indian Defense", 'variation': '1.d4 Nf6 2.c4 e6 3.Nf3 b6', 'moves': ['d4', 'Nf6', 'c4', 'e6', 'Nf3', 'b6'], 'description': '后翼印度防御，以侧翼兵控制中心', 'category': 'E'},
    {'eco_code': 'E60', "name": "King's Indian Defense", 'variation': '1.d4 Nf6 2.c4 g6 3.Nc3 Bg7', 'moves': ['d4', 'Nf6', 'c4', 'g6', 'Nc3', 'Bg7'], 'description': '国王印度防御，卡帕布兰卡之后的经典反击型开局', 'category': 'E'},
    {'eco_code': 'E94', "name": "King's Indian: Classical", 'variation': '1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.Nf3 O-O 6.Be2 e5', 'moves': ['d4', 'Nf6', 'c4', 'g6', 'Nc3', 'Bg7', 'e4', 'd6', 'Nf3', 'O-O', 'Be2', 'e5'], 'description': '国王印度防御经典变例，卡什帕罗夫的利器', 'category': 'E'},
    {'eco_code': 'E11', "name": "Bogo-Indian Defense", 'variation': '1.d4 Nf6 2.c4 e6 3.Nf3 Bb4+', 'moves': ['d4', 'Nf6', 'c4', 'e6', 'Nf3', 'Bb4+'], 'description': '波戈印度防御，以Bb4+将军为特征', 'category': 'E'},
    {'eco_code': 'B12', 'name': 'Caro-Kann Defense: Advance', 'variation': '1.e4 c6 2.d4 d5 3.e5', 'moves': ['e4', 'c6', 'd4', 'd5', 'e5'], 'description': '卡罗-卡恩防御推进变例，稳固而富有策略性', 'category': 'B'},
    {'eco_code': 'C11', 'name': 'French Defense', 'variation': '1.e4 e6 2.d4 d5', 'moves': ['e4', 'e6', 'd4', 'd5'], 'description': '法兰西防御，以坚固的结构和反击机会著称', 'category': 'C'},
]

PLAYERS_DATA = [
    {'name': 'Magnus Carlsen', 'title': 'GM', 'country': 'Norway', 'elo_rating': 2830, 'birth_date': '1990-11-30'},
    {'name': 'Garry Kasparov', 'title': 'GM', 'country': 'Russia', 'elo_rating': 2851, 'birth_date': '1963-04-13'},
    {'name': 'Bobby Fischer', 'title': 'GM', 'country': 'USA', 'elo_rating': 2785, 'birth_date': '1943-03-09'},
    {'name': 'Anatoly Karpov', 'title': 'GM', 'country': 'Russia', 'elo_rating': 2780, 'birth_date': '1951-05-23'},
    {'name': 'Viswanathan Anand', 'title': 'GM', 'country': 'India', 'elo_rating': 2770, 'birth_date': '1969-12-11'},
    {'name': 'Vladimir Kramnik', 'title': 'GM', 'country': 'Russia', 'elo_rating': 2777, 'birth_date': '1975-06-25'},
    {'name': 'Fabiano Caruana', 'title': 'GM', 'country': 'USA', 'elo_rating': 2795, 'birth_date': '1992-07-30'},
    {'name': 'Ding Liren', 'title': 'GM', 'country': 'China', 'elo_rating': 2780, 'birth_date': '1992-10-24'},
    {'name': 'Mikhail Tal', 'title': 'GM', 'country': 'Latvia', 'elo_rating': 2705, 'birth_date': '1936-11-09'},
    {'name': 'Jose Raul Capablanca', 'title': 'GM', 'country': 'Cuba', 'elo_rating': 2725, 'birth_date': '1888-11-19'},
    {'name': 'Alexander Alekhine', 'title': 'GM', 'country': 'Russia', 'elo_rating': 2690, 'birth_date': '1892-10-31'},
    {'name': 'Hikaru Nakamura', 'title': 'GM', 'country': 'USA', 'elo_rating': 2788, 'birth_date': '1987-12-09'},
    {'name': 'Boris Spassky', 'title': 'GM', 'country': 'Russia', 'elo_rating': 2690, 'birth_date': '1937-01-30'},
]

TOURNAMENTS_DATA = [
    {'name': 'World Chess Championship 1972', 'start_date': '1972-07-11', 'end_date': '1972-09-01', 'location': 'Reykjavik, Iceland', 'category': 'World Championship'},
    {'name': 'World Chess Championship 1985', 'start_date': '1985-09-03', 'end_date': '1985-11-09', 'location': 'Moscow, Russia', 'category': 'World Championship'},
    {'name': 'Tata Steel 2023', 'start_date': '2023-01-13', 'end_date': '2023-01-29', 'location': 'Wijk aan Zee, Netherlands', 'category': 'Super Tournament'},
    {'name': 'Candidates Tournament 2024', 'start_date': '2024-04-03', 'end_date': '2024-04-25', 'location': 'Toronto, Canada', 'category': 'Candidates'},
]

GAMES_DATA = [
    {
        'white': 'Bobby Fischer', 'black': 'Boris Spassky',
        'white_elo': 2785, 'black_elo': 2690,
        'tournament': 'World Chess Championship 1972',
        'date': '1972-07-11', 'result': '1-0', 'eco_code': 'C41',
        'opening_name': 'Philidor Defense',
        'pgn': '[Event "World Championship 1972"]\n[Site "Reykjavik"]\n[Date "1972.07.11"]\n[Round "1"]\n[White "Fischer, Robert"]\n[Black "Spassky, Boris"]\n[Result "1-0"]\n[WhiteElo "2785"]\n[BlackElo "2690"]\n[ECO "C41"]\n\n1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0',
        'total_moves': 34,
    },
    {
        'white': 'Garry Kasparov', 'black': 'Anatoly Karpov',
        'white_elo': 2851, 'black_elo': 2780,
        'tournament': 'World Chess Championship 1985',
        'date': '1985-09-03', 'result': '1-0', 'eco_code': 'E94',
        'opening_name': "King's Indian: Classical",
        'pgn': '[Event "World Championship 1985"]\n[Site "Moscow"]\n[Date "1985.09.03"]\n[Round "1"]\n[White "Kasparov, Garry"]\n[Black "Karpov, Anatoly"]\n[Result "1-0"]\n[ECO "E94"]\n\n1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3 O-O 6. Be2 e5 7. O-O Nc6 8. d5 Ne7 9. Ne1 Nd7 10. Be3 f5 11. f3 f4 12. Bf2 g5 13. Rc1 Ng6 14. c5 Nf6 15. Nb5 a6 16. Nc3 bxc5 17. Rxc5 Ne8 18. Nd3 g4 19. fxg4 Nxg4 20. Bg1 Nf6 21. Qc2 Nh5 22. Nf2 Bd7 23. Rcc1 Rb8 24. b3 Rb5 25. Nd2 Bf5 26. Qc4 Qd7 27. a4 Rb8 28. Nb1 Nh4 29. Nc3 Bg6 30. Qd3 Nf5 31. Bf1 Nh4 32. Nd2 Bf7 33. Nf3 Nf5 34. Bg1 a5 35. Nd2 Nh4 36. Nf3 Nf5 37. Nd2 Nh4 38. Nf3 Nf5 39. Nd2 1-0',
        'total_moves': 39,
    },
    {
        'white': 'Magnus Carlsen', 'black': 'Fabiano Caruana',
        'white_elo': 2830, 'black_elo': 2795,
        'tournament': 'Tata Steel 2023',
        'date': '2023-01-15', 'result': '1/2-1/2', 'eco_code': 'D85',
        'opening_name': 'Grünfeld Defense',
        'pgn': '[Event "Tata Steel 2023"]\n[Site "Wijk aan Zee"]\n[Date "2023.01.15"]\n[Round "4"]\n[White "Carlsen, Magnus"]\n[Black "Caruana, Fabiano"]\n[Result "1/2-1/2"]\n[ECO "D85"]\n\n1. d4 Nf6 2. c4 g6 3. Nc3 d5 4. cxd5 Nxd5 5. e4 Nxc3 6. bxc3 Bg7 7. Nf3 c5 8. Be2 Nc6 9. Be3 O-O 10. O-O Qc7 11. Qd2 Rd8 12. Rfd1 b6 13. d5 Na5 14. Qc2 Bb7 15. Nd4 e6 16. dxe6 fxe6 17. Nf3 Rdf8 18. Nd2 Bd5 19. Rab1 Rac8 20. f3 Qd7 21. Qb3 Qe8 22. a4 Be7 23. Bf1 Bc6 24. Qa2 Qd7 25. Nb3 Nc4 26. Bxc4 Bxc4 27. Nd2 Be6 28. Nf1 Rfd8 29. Nd2 Rxd1+ 30. Rxd1 Rd8 31. Rxd8+ Qxd8 32. Qb3 Qd7 33. Qxb6 Qxb5 34. axb5 Bf6 35. Qa5 Bd8 36. Qa8 Bd5 37. Qa2 Be7 38. Qa5 Bc6 39. Qa8 Bd5 40. Qa2 1/2-1/2',
        'total_moves': 40,
    },
    {
        'white': 'Ding Liren', 'black': 'Hikaru Nakamura',
        'white_elo': 2780, 'black_elo': 2788,
        'tournament': 'Candidates Tournament 2024',
        'date': '2024-04-05', 'result': '1-0', 'eco_code': 'B90',
        'opening_name': 'Sicilian Najdorf',
        'pgn': '[Event "Candidates 2024"]\n[Site "Toronto"]\n[Date "2024.04.05"]\n[Round "3"]\n[White "Ding Liren"]\n[Black "Nakamura, Hikaru"]\n[Result "1-0"]\n[ECO "B90"]\n\n1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be3 e5 7. Nb3 Be6 8. f3 Be7 9. Qd2 O-O 10. O-O-O Nbd7 11. g4 b5 12. g5 b4 13. Nd5 Nxd5 14. exd5 Bf5 15. Qxb4 Rb8 16. Qa4 Bxd5 17. Bxd5 Nc5 18. Qa5 Rb5 19. Qa3 e4 20. Nxc5 dxc5 21. fxe4 Bc4 22. Bd2 Qb6 23. Bc3 Rfb8 24. b3 Bb5 25. a4 Bc6 26. Bxb5 axb5 27. axb5 Rxb5 28. Ra5 R8b7 29. Rha1 h6 30. gxh6 Qd4 31. Qxd4 cxd4 32. Bxd4 Rb1 33. R1a2 R1b4 34. c3 R4b5 35. Ra8+ Kh7 36. R8a7 R5b7 37. Rxb7 Rxb7 38. Kc2 g5 39. Kd3 Kg6 40. c4 f5 41. exf5+ Kxf5 42. Ke3 Kg4 43. Rd7 Rb3+ 44. Ke2 Kxh6 45. Rd6+ Kg7 46. Rxg6+ Kf7 47. Rg5 Ke6 48. Rxg5 Rxb3 49. Rg6+ Kd7 50. Rg7+ Ke8 51. Rg8+ Kd7 52. Rd8+ Ke6 53. Rd6+ Ke7 54. Rd5 Rb2+ 55. Ke3 Rb3+ 56. Kd4 Rb2 57. Rd6 Ke8 58. c5 Rb5 59. c6 Kf7 60. c7 Rxc7 61. Rd7 Rxd7 62. Kxd7 1-0',
        'total_moves': 62,
    },
    {
        'white': 'Mikhail Tal', 'black': 'Bobby Fischer',
        'white_elo': 2705, 'black_elo': 2785,
        'tournament': 'World Chess Championship 1972',
        'date': '1960-11-07', 'result': '1-0', 'eco_code': 'C84',
        'opening_name': 'Ruy Lopez: Closed',
        'pgn': '[Event "Leipzig Olympiad"]\n[Site "Leipzig"]\n[Date "1960.11.07"]\n[Round "7"]\n[White "Tal, Mikhail"]\n[Black "Fischer, Robert"]\n[Result "1-0"]\n[ECO "C84"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 11. Nbd2 Bb7 12. Bc2 Re8 13. Nf1 Bf8 14. Ng3 g6 15. a4 Bg7 16. Bd3 c6 17. Bg5 Qc7 18. Qd2 Nh5 19. Nxh5 gxh5 20. Bh6 Bxh6 21. Qxh6 Qd8 22. axb5 axb5 23. Rxa8 Bxa8 24. Bh7+ Kf8 25. d5 cxd5 26. exd5 Nf6 27. Bc2 Qb6 28. Nd4 exd4 29. cxd4 Qxd4 30. Rf1 Ke7 31. Qg7 Rg8 32. Qxh7 Nxd5 33. Qg6 Rf8 34. Re1+ Kd7 35. Qf5+ Kc6 36. Re6+ Kb5 37. Qxd5+ Ka4 38. b3+ Ka3 39. Re3+ Kb4 40. Qd2 1-0',
        'total_moves': 40,
    },
]


def seed_openings():
    click.echo('Seeding openings...')
    for data in OPENINGS_DATA:
        existing = Opening.query.filter_by(eco_code=data['eco_code']).first()
        if existing:
            continue
        opening = Opening(
            eco_code=data['eco_code'],
            name=data['name'],
            variation=data['variation'],
            description=data['description'],
            category=data['category'],
        )
        opening.set_moves(data['moves'])
        db.session.add(opening)
    db.session.commit()
    click.echo(f'  Seeded {len(OPENINGS_DATA)} openings.')


def seed_players():
    click.echo('Seeding players...')
    for data in PLAYERS_DATA:
        existing = Player.query.filter_by(name=data['name']).first()
        if existing:
            continue
        player = Player(
            name=data['name'],
            title=data['title'],
            country=data['country'],
            elo_rating=data['elo_rating'],
            birth_date=data['birth_date'],
        )
        db.session.add(player)
    db.session.commit()
    click.echo(f'  Seeded {len(PLAYERS_DATA)} players.')


def seed_tournaments():
    click.echo('Seeding tournaments...')
    for data in TOURNAMENTS_DATA:
        existing = Tournament.query.filter_by(name=data['name']).first()
        if existing:
            continue
        tournament = Tournament(
            name=data['name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            location=data['location'],
            category=data['category'],
        )
        db.session.add(tournament)
    db.session.commit()
    click.echo(f'  Seeded {len(TOURNAMENTS_DATA)} tournaments.')


def seed_games():
    click.echo('Seeding games...')
    for data in GAMES_DATA:
        white = Player.query.filter_by(name=data['white']).first()
        black = Player.query.filter_by(name=data['black']).first()
        tournament = Tournament.query.filter_by(name=data['tournament']).first()
        if not white or not black:
            click.echo(f'  Skipped {data["white"]} vs {data["black"]}: player not found')
            continue
        existing = Game.query.filter_by(
            white_player_id=white.id,
            black_player_id=black.id,
            date=data['date'],
        ).first()
        if existing:
            continue
        game = Game(
            white_player_id=white.id,
            black_player_id=black.id,
            tournament_id=tournament.id if tournament else None,
            date=data['date'],
            result=data['result'],
            pgn_content=data['pgn'],
            eco_code=data['eco_code'],
            opening_name=data['opening_name'],
            total_moves=data['total_moves'],
            white_elo=data.get('white_elo'),
            black_elo=data.get('black_elo'),
        )
        db.session.add(game)
    db.session.commit()
    click.echo(f'  Seeded {len(GAMES_DATA)} games.')


def seed_admin():
    click.echo('Seeding admin user...')
    existing = User.query.filter_by(username='admin').first()
    if existing:
        click.echo('  Admin user already exists.')
        return
    admin = User(username='admin', email='admin@chessdb.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    click.echo('  Admin user created (username: admin, password: admin123).')


def init_db():
    db.create_all()
    click.echo('Database tables created.')


def reset_db():
    db.drop_all()
    db.create_all()
    click.echo('Database reset.')


def seed_data():
    seed_openings()
    seed_players()
    seed_tournaments()
    seed_games()
    seed_admin()
    click.echo('All seed data inserted.')


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    with app.app_context():
        init_db()
        seed_data()
